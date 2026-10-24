"""Debate router: create, fetch, start, invite lookup, and full state snapshot."""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db
from ..services.debate_engine import start_debate_engine
from ..websockets import ws_manager

router = APIRouter(prefix="/api/debates", tags=["debates"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def _format_dt(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


@router.post("", response_model=schemas.DebateCreateResponse)
def create_debate(payload: schemas.DebateCreate, db: Session = Depends(get_db)):
    """Create a debate, generate invite link, and return creator token."""
    debate, invite = crud.create_debate(
        db=db,
        topic=payload.topic,
        description=payload.description,
        tone=payload.tone,
        duration_secs=payload.duration_secs,
    )

    invite_url = f"{FRONTEND_URL}/join/{invite.uuid}"

    return schemas.DebateCreateResponse(
        debate_id=debate.id,
        invite_url=invite_url,
        creator_token=debate.creator_token,
        agent_a=schemas.AgentInfo(name=debate.agent_a_name, model=debate.model_a),
        agent_b=schemas.AgentInfo(name=debate.agent_b_name, model=debate.model_b),
    )


@router.get("/invite/{uuid}")
def get_debate_by_invite(uuid: str, db: Session = Depends(get_db)):
    """Get debate metadata by invite UUID for viewer landing page."""
    debate = crud.get_debate_by_invite(db, uuid)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate invite not found or expired")

    return {
        "id": debate.id,
        "topic": debate.topic,
        "description": debate.description,
        "tone": debate.tone,
        "agent_a_name": debate.agent_a_name,
        "agent_b_name": debate.agent_b_name,
        "model_a": debate.model_a,
        "model_b": debate.model_b,
        "duration_secs": debate.duration_secs,
        "status": debate.status,
    }


@router.get("/{debate_id}", response_model=schemas.DebateResponse)
def get_debate(debate_id: int, db: Session = Depends(get_db)):
    """Get full debate record."""
    debate = crud.get_debate(db, debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")

    return schemas.DebateResponse(
        id=debate.id,
        topic=debate.topic,
        description=debate.description or "",
        tone=debate.tone,
        agent_a_name=debate.agent_a_name,
        agent_b_name=debate.agent_b_name,
        model_a=debate.model_a,
        model_b=debate.model_b,
        duration_secs=debate.duration_secs,
        status=debate.status,
        created_at=_format_dt(debate.created_at) or "",
        starts_at=_format_dt(debate.starts_at),
        ends_at=_format_dt(debate.ends_at),
        winner=debate.winner,
    )


@router.get("/{debate_id}/state")
def get_debate_state(
    debate_id: int,
    viewer_id: Optional[str] = Query(None),
    x_viewer_id: Optional[str] = Header(None, alias="X-Viewer-Id"),
    db: Session = Depends(get_db),
):
    """Full snapshot: debate + all rounds + vote counts + viewer's vote (for late joiner/reconnect)."""
    debate = crud.get_debate(db, debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")

    effective_viewer_id = viewer_id or x_viewer_id

    rounds = crud.get_rounds(db, debate_id)
    rounds_data = [
        {
            "round": r.round_number,
            "label": r.label,
            "agent": r.agent,
            "argument": r.argument,
            "citations": r.citations or [],
        }
        for r in rounds
    ]

    vote_counts = crud.get_vote_counts(db, debate_id)
    viewer_vote = (
        crud.get_viewer_vote(db, debate_id, effective_viewer_id)
        if effective_viewer_id
        else None
    )

    # Compute remaining seconds if running
    seconds_left = debate.duration_secs
    if debate.status == "running" and debate.starts_at and debate.ends_at:
        now = datetime.now(timezone.utc)
        ends = debate.ends_at
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        remaining = int((ends - now).total_seconds())
        seconds_left = max(0, remaining)
    elif debate.status == "finished":
        seconds_left = 0

    return {
        "type": "state_snapshot",
        "debate": {
            "id": debate.id,
            "topic": debate.topic,
            "description": debate.description or "",
            "tone": debate.tone,
            "status": debate.status,
            "seconds_left": seconds_left,
            "total_seconds": debate.duration_secs,
            "winner": debate.winner,
        },
        "agents": {
            "A": {"name": debate.agent_a_name, "model": debate.model_a},
            "B": {"name": debate.agent_b_name, "model": debate.model_b},
        },
        "rounds_so_far": rounds_data,
        "current_vote_counts": vote_counts,
        "viewer_vote": viewer_vote,
    }


@router.post("/{debate_id}/start")
async def start_debate(
    debate_id: int,
    x_creator_token: Optional[str] = Header(None, alias="X-Creator-Token"),
    db: Session = Depends(get_db),
):
    """Start debate (requires X-Creator-Token). Launches debate engine background task."""
    debate = crud.get_debate(db, debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")

    if not x_creator_token or debate.creator_token != x_creator_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Creator-Token",
        )

    if debate.status != "draft":
        return {
            "status": debate.status,
            "ends_at": _format_dt(debate.ends_at) or "",
            "message": "Debate is already started or finished",
        }

    debate = crud.start_debate(db, debate)

    # Broadcast debate_started event to waiting viewers
    await ws_manager.broadcast(
        debate_id,
        {
            "type": "debate_started",
            "starts_at": _format_dt(debate.starts_at),
            "ends_at": _format_dt(debate.ends_at),
        },
    )

    # Launch engine
    start_debate_engine(debate_id)

    return {
        "status": debate.status,
        "ends_at": _format_dt(debate.ends_at) or "",
    }
