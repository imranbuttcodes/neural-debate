"""Debate Engine: orchestrates ticker, rounds, token streaming, and voting windows."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List

from .. import crud
from ..agents.debate_graph import run_debate_agent
from ..agents.state import DebateState, PreviousArgument, SearchResult
from ..db import SessionLocal
from ..websockets import ws_manager

logger = logging.getLogger(__name__)

VOTING_WINDOW_SECS = int(os.getenv("VOTING_WINDOW_SECS", "15"))

# Active debate engine tasks by debate_id to prevent duplicates
_active_debates: Dict[int, asyncio.Task] = {}


ROUNDS_SCHEDULE = [
    {"round": 1, "agent": "A", "label": "Opening", "position": "FOR"},
    {"round": 2, "agent": "B", "label": "Rebuttal", "position": "AGAINST"},
    {"round": 3, "agent": "A", "label": "Closing", "position": "FOR"},
    {"round": 4, "agent": "B", "label": "Closing", "position": "AGAINST"},
]


async def _run_ticker(debate_id: int, duration_secs: int, stop_event: asyncio.Event):
    """Broadcasts timer_tick every 1s until duration expires or stop_event is set."""
    seconds_left = duration_secs
    while seconds_left > 0 and not stop_event.is_set():
        await ws_manager.broadcast(
            debate_id,
            {
                "type": "timer_tick",
                "seconds_left": seconds_left,
                "total_seconds": duration_secs,
            },
        )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)
            break
        except asyncio.TimeoutError:
            seconds_left -= 1

    if seconds_left <= 0:
        await ws_manager.broadcast(
            debate_id,
            {
                "type": "timer_tick",
                "seconds_left": 0,
                "total_seconds": duration_secs,
            },
        )


async def run_debate_lifecycle(debate_id: int):
    """Main lifecycle coroutine managing ticker and rounds."""
    db = SessionLocal()
    try:
        debate = crud.get_debate(db, debate_id)
        if not debate:
            logger.error(f"Debate {debate_id} not found")
            return

        duration_secs = debate.duration_secs or 300
        stop_event = asyncio.Event()

        # Start background ticker
        ticker_task = asyncio.create_task(_run_ticker(debate_id, duration_secs, stop_event))

        previous_arguments: List[PreviousArgument] = []
        rounds_breakdown = []

        start_time = datetime.now(timezone.utc)

        for sched in ROUNDS_SCHEDULE:
            # Check if duration expired
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed >= duration_secs:
                logger.info(f"Debate {debate_id} timed out before round {sched['round']}")
                break

            round_num = sched["round"]
            agent_key = sched["agent"]
            label = sched["label"]
            position = sched["position"]

            agent_name = debate.agent_a_name if agent_key == "A" else debate.agent_b_name
            model_name = debate.model_a if agent_key == "A" else debate.model_b

            # 1. Broadcast round_start
            await ws_manager.broadcast(
                debate_id,
                {
                    "type": "round_start",
                    "round": round_num,
                    "label": label,
                    "agent": agent_key,
                    "agent_name": agent_name,
                    "model": model_name,
                },
            )

            # 2. Broadcast agent_thinking
            await ws_manager.broadcast(
                debate_id,
                {
                    "type": "agent_thinking",
                    "agent": agent_key,
                    "round": round_num,
                    "message": f"{agent_name} is researching sources and formulating arguments...",
                },
            )

            # Record round start in DB
            db_round = crud.create_round(
                db=db,
                debate_id=debate_id,
                round_number=round_num,
                label=label,
                agent=agent_key,
                model_name=model_name,
                search_query=f"{debate.topic} {label}",
            )

            # 3. Prepare state & streaming callback
            state = DebateState(
                topic=debate.topic,
                description=debate.description or "",
                tone=debate.tone,
                model_name=model_name,
                agent=agent_key,
                agent_name=agent_name,
                round_number=round_num,
                label=label,
                position=position,
                previous_arguments=previous_arguments,
            )

            async def token_callback(token: str):
                await ws_manager.broadcast(
                    debate_id,
                    {
                        "type": "argument_token",
                        "agent": agent_key,
                        "round": round_num,
                        "token": token,
                    },
                )

            # 4. Run debate agent
            state_result = await run_debate_agent(state, token_callback=token_callback)

            # 5. Update round in DB & broadcast argument_done
            citations_dict = [c.model_dump() for c in state_result.citations]
            crud.update_round(
                db=db,
                round_id=db_round.id,
                argument=state_result.argument,
                citations=citations_dict,
            )

            await ws_manager.broadcast(
                debate_id,
                {
                    "type": "argument_done",
                    "agent": agent_key,
                    "round": round_num,
                    "full_text": state_result.argument,
                    "citations": citations_dict,
                },
            )

            # Add to previous arguments memory for subsequent turns
            previous_arguments.append(
                PreviousArgument(
                    round_number=round_num,
                    label=label,
                    agent=agent_key,
                    agent_name=agent_name,
                    text=state_result.argument,
                )
            )

            # 6. Voting window
            await ws_manager.broadcast(
                debate_id,
                {
                    "type": "voting_open",
                    "round": round_num,
                    "message": "Audience voting is live. You can cast or switch your vote.",
                },
            )

            # Wait for voting window seconds (checking elapsed time)
            vote_window_remaining = VOTING_WINDOW_SECS
            while vote_window_remaining > 0:
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                if elapsed >= duration_secs:
                    break
                await asyncio.sleep(1)
                vote_window_remaining -= 1

            # 7. Close voting for round & record breakdown
            counts = crud.get_vote_counts(db, debate_id)
            await ws_manager.broadcast(
                debate_id,
                {
                    "type": "voting_closed",
                    "round": round_num,
                    "A": counts["A"],
                    "B": counts["B"],
                    "total": counts["total"],
                },
            )

            rounds_breakdown.append(
                {
                    "round": round_num,
                    "label": label,
                    "agent": agent_key,
                    "A": counts["A"],
                    "B": counts["B"],
                }
            )

        # Stop ticker
        stop_event.set()
        await ticker_task

        # 8. Determine Winner
        final_counts = crud.get_vote_counts(db, debate_id)
        if final_counts["A"] > final_counts["B"]:
            winner = "A"
            winner_name = debate.agent_a_name
            is_tie = False
        elif final_counts["B"] > final_counts["A"]:
            winner = "B"
            winner_name = debate.agent_b_name
            is_tie = False
        else:
            winner = "TIE"
            winner_name = "Draw"
            is_tie = True

        crud.finish_debate(db, debate_id, winner)

        await ws_manager.broadcast(
            debate_id,
            {
                "type": "finished",
                "winner": winner,
                "winner_name": winner_name,
                "is_tie": is_tie,
                "final_votes": final_counts,
                "rounds_breakdown": rounds_breakdown,
            },
        )

    except Exception as e:
        logger.exception(f"Error in debate engine for debate {debate_id}: {e}")
        await ws_manager.broadcast(
            debate_id,
            {
                "type": "agent_error",
                "message": f"Debate engine encountered an error: {str(e)}",
            },
        )
    finally:
        _active_debates.pop(debate_id, None)
        db.close()


def start_debate_engine(debate_id: int):
    """Spawns run_debate_lifecycle in the background."""
    if debate_id in _active_debates and not _active_debates[debate_id].done():
        logger.warning(f"Debate {debate_id} engine already running")
        return
    task = asyncio.create_task(run_debate_lifecycle(debate_id))
    _active_debates[debate_id] = task
