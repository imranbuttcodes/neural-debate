"""Simple web app: create a debate, invite viewers, watch live, vote, winner."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..debate.graph import AGENTS, run_debate

STATIC = Path(__file__).resolve().parents[2] / "static"
INDEX = STATIC / "index.html"
PAUSE_SECONDS = float(os.getenv("WEB_PAUSE_SECONDS", "4.5"))

app = FastAPI(title="AI Debate Arena")
ROOMS: dict[str, "Room"] = {}


class DebateCreate(BaseModel):
    topic: str
    seconds: int = 120


class ViewerCreate(BaseModel):
    name: str
    emoji: str = "🦊"


class VoteIn(BaseModel):
    agent: str


def _agents_meta() -> dict:
    return {
        side: {"name": AGENTS[side].name, "model": AGENTS[side].model}
        for side in ("A", "B")
    }


class Room:
    """One debate: viewers, votes, transcript and the engine thread."""

    def __init__(self, topic: str, seconds: int):
        self.id = uuid.uuid4().hex[:8]
        self.topic = topic
        self.seconds = max(20, min(int(seconds), 300))
        self.host_token = secrets.token_urlsafe(12)
        self.status = "waiting"          # waiting -> running -> finished
        self.started_at: Optional[float] = None
        self.viewers: dict[str, dict] = {}
        self.votes: dict[str, str] = {}
        self.transcript: list[dict] = []
        self.winner: Optional[dict] = None
        self.clients: dict[str, WebSocket] = {}

        self.loop = asyncio.get_running_loop()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.broadcast_task = asyncio.create_task(self._broadcast())

    # ── events ────────────────────────────────────────────────────────
    def emit(self, event: dict) -> None:
        """Called from the engine thread; hands the event to the asyncio loop."""
        if self.loop.is_closed():
            return
        self.loop.call_soon_threadsafe(self._enqueue, event)

    def _enqueue(self, event: dict) -> None:
        try:
            self.queue.put_nowait(event)
        except Exception:  # noqa: BLE001 - loop shutting down
            pass

    async def _broadcast(self) -> None:
        while True:
            event = await self.queue.get()
            if event is None:
                return
            if event["type"] == "turn_end":
                self.transcript.append(
                    {
                        "agent": event["agent"],
                        "name": event["name"],
                        "turn": event["turn"],
                        "text": event["text"],
                    }
                )
            if event["type"] == "finished":
                self.winner = event["winner"]
            payload = json.dumps(event, ensure_ascii=False)
            for cid, ws in list(self.clients.items()):
                try:
                    await ws.send_text(payload)
                except Exception:  # noqa: BLE001
                    self.clients.pop(cid, None)

    # ── state ─────────────────────────────────────────────────────────
    def counts(self) -> dict:
        a = sum(1 for vote in self.votes.values() if vote == "A")
        return {"A": a, "B": len(self.votes) - a, "total": len(self.votes)}

    def result(self) -> dict:
        votes = self.counts()
        if votes["A"] == votes["B"]:
            return {"agent": "TIE", "name": "Draw", "votes": votes}
        side = "A" if votes["A"] > votes["B"] else "B"
        return {"agent": side, "name": AGENTS[side].name, "votes": votes}

    def voters_payload(self) -> list[dict]:
        """Every joined viewer plus their vote, voters first."""
        rows = [
            {
                "id": viewer_id,
                "name": viewer["name"],
                "emoji": viewer["emoji"],
                "agent": self.votes.get(viewer_id),
            }
            for viewer_id, viewer in self.viewers.items()
        ]
        rows.sort(key=lambda row: row["agent"] is None)
        return rows

    def viewer_list(self) -> list[dict]:
        return [
            {"id": v["id"], "name": v["name"], "emoji": v["emoji"], "online": v["online"]}
            for v in self.viewers.values()
        ]

    def seconds_left(self) -> int:
        if self.status == "waiting":
            return self.seconds
        if self.status == "finished" or not self.started_at:
            return 0
        return max(0, int(round(self.seconds - (time.time() - self.started_at))))

    def snapshot(self, viewer_id: Optional[str]) -> dict:
        return {
            "type": "snapshot",
            "debate": {
                "id": self.id,
                "topic": self.topic,
                "seconds": self.seconds,
                "status": self.status,
                "agents": _agents_meta(),
            },
            "seconds_left": self.seconds_left(),
            "transcript": self.transcript,
            "votes": self.counts(),
            "voters": self.voters_payload(),
            "your_vote": self.votes.get(viewer_id) if viewer_id else None,
            "viewers": self.viewer_list(),
            "winner": self.winner,
        }

    # ── engine ────────────────────────────────────────────────────────
    async def tick(self) -> None:
        while self.status == "running":
            self._enqueue({"type": "tick", "seconds_left": self.seconds_left()})
            # If a model call hangs past the budget, force the result anyway.
            overrun = time.time() - (self.started_at or time.time()) - self.seconds
            if self.seconds_left() <= 0 and overrun > 30:
                self.status = "finished"
                self.winner = self.result()
                self._enqueue(
                    {"type": "finished", "winner": self.winner, "votes": self.counts()}
                )
                return
            await asyncio.sleep(1)

    def run_engine(self) -> None:
        try:
            run_debate(
                self.topic,
                seconds=self.seconds,
                max_turns=999,
                emit=self.emit,
                verbose=False,
                pause=PAUSE_SECONDS,
            )
        except Exception as exc:  # noqa: BLE001 - surface it to the room
            self.emit({"type": "error", "message": f"engine failed: {exc}"})
        finally:
            self.status = "finished"
            self.emit(
                {
                    "type": "finished",
                    "winner": self.result(),
                    "votes": self.counts(),
                    "voters": self.voters_payload(),
                }
            )


def _room(debate_id: str) -> Room:
    room = ROOMS.get(debate_id)
    if not room:
        raise HTTPException(status_code=404, detail="Debate not found")
    return room


# ── REST ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "debates": len(ROOMS)}


@app.post("/api/debates")
async def create_debate(payload: DebateCreate) -> dict:
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    room = Room(topic, payload.seconds)
    ROOMS[room.id] = room
    return {
        "id": room.id,
        "topic": room.topic,
        "seconds": room.seconds,
        "status": room.status,
        "agents": _agents_meta(),
        "host_token": room.host_token,
        "invite_url": f"/join/{room.id}",
    }


@app.get("/api/debates/{debate_id}")
async def get_debate(debate_id: str) -> dict:
    room = _room(debate_id)
    return {
        "id": room.id,
        "topic": room.topic,
        "seconds": room.seconds,
        "status": room.status,
        "agents": _agents_meta(),
        "votes": room.counts(),
        "viewers": len(room.viewers),
        "winner": room.winner,
    }


@app.post("/api/debates/{debate_id}/viewers")
async def join_debate(debate_id: str, payload: ViewerCreate) -> dict:
    room = _room(debate_id)
    viewer_id = uuid.uuid4().hex[:10]
    viewer = {
        "id": viewer_id,
        "name": payload.name.strip()[:24] or "Viewer",
        "emoji": (payload.emoji or "🦊")[:4],
        "online": False,
    }
    room.viewers[viewer_id] = viewer
    room._enqueue(
        {
            "type": "viewers",
            "viewers": room.viewer_list(),
            "voters": room.voters_payload(),
        }
    )
    return {"viewer_id": viewer_id, "name": viewer["name"], "emoji": viewer["emoji"]}


@app.post("/api/debates/{debate_id}/start")
async def start_debate(
    debate_id: str, x_host_token: Optional[str] = Header(None)
) -> dict:
    room = _room(debate_id)
    if not x_host_token or x_host_token != room.host_token:
        raise HTTPException(status_code=403, detail="Host token required")
    if room.status != "waiting":
        return {"status": room.status}

    room.status = "running"
    room.started_at = time.time()
    room._enqueue({"type": "started"})
    asyncio.create_task(room.tick())
    threading.Thread(target=room.run_engine, daemon=True).start()
    return {"status": "running"}


@app.post("/api/debates/{debate_id}/vote")
async def cast_vote(
    debate_id: str,
    payload: VoteIn,
    x_viewer_id: Optional[str] = Header(None),
) -> dict:
    room = _room(debate_id)
    if room.status != "running":
        raise HTTPException(status_code=400, detail="Voting is closed")
    if payload.agent not in ("A", "B"):
        raise HTTPException(status_code=400, detail="Vote must be A or B")
    if not x_viewer_id or x_viewer_id not in room.viewers:
        raise HTTPException(status_code=403, detail="Join the debate to vote")

    room.votes[x_viewer_id] = payload.agent
    room._enqueue(
        {
            "type": "votes",
            "votes": room.counts(),
            "voters": room.voters_payload(),
        }
    )
    return {"ok": True, "votes": room.counts()}


# ── WebSocket ─────────────────────────────────────────────────────────
@app.websocket("/ws/debates/{debate_id}")
async def debate_socket(
    websocket: WebSocket, debate_id: str, viewer_id: Optional[str] = Query(None)
) -> None:
    room = ROOMS.get(debate_id)
    if not room:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    client_id = uuid.uuid4().hex
    room.clients[client_id] = websocket
    viewer = room.viewers.get(viewer_id) if viewer_id else None
    if viewer:
        viewer["online"] = True
        room._enqueue(
            {
                "type": "viewers",
                "viewers": room.viewer_list(),
                "voters": room.voters_payload(),
            }
        )

    try:
        await websocket.send_text(json.dumps(room.snapshot(viewer_id), ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        pass
    finally:
        room.clients.pop(client_id, None)
        if viewer:
            viewer["online"] = False
            room._enqueue(
                {
                    "type": "viewers",
                    "viewers": room.viewer_list(),
                    "voters": room.voters_payload(),
                }
            )


# ── pages ─────────────────────────────────────────────────────────────
@app.get("/")
async def home() -> FileResponse:
    return FileResponse(INDEX)


@app.get("/join/{debate_id}")
async def join_page(debate_id: str) -> FileResponse:
    return FileResponse(INDEX)


@app.get("/host/{debate_id}")
async def host_page(debate_id: str) -> FileResponse:
    return FileResponse(INDEX)
