"""Vote router: cast/change votes with UPSERT semantics and live WS broadcasts."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db
from ..websockets import ws_manager

router = APIRouter(prefix="/api/votes", tags=["votes"])


async def _handle_vote_upsert(
    payload: schemas.VoteCreate,
    viewer_id: Optional[str],
    db: Session,
):
    if not viewer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Viewer-Id header",
        )

    if payload.vote not in ("A", "B"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vote must be 'A' or 'B'",
        )

    debate = crud.get_debate(db, payload.debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")

    changed = crud.upsert_vote(
        db=db,
        debate_id=payload.debate_id,
        viewer_id=viewer_id,
        vote=payload.vote,
    )

    counts = crud.get_vote_counts(db, payload.debate_id)

    # Broadcast live update to ALL viewers if vote changed or was inserted
    if changed:
        await ws_manager.broadcast(
            payload.debate_id,
            {
                "type": "live_vote_update",
                "A": counts["A"],
                "B": counts["B"],
                "total": counts["total"],
                "percent_A": counts["percent_A"],
                "percent_B": counts["percent_B"],
            },
        )

    return schemas.VoteResponse(
        ok=True,
        A=counts["A"],
        B=counts["B"],
        total=counts["total"],
    )


@router.post("", response_model=schemas.VoteResponse)
async def cast_vote(
    payload: schemas.VoteCreate,
    x_viewer_id: Optional[str] = Header(None, alias="X-Viewer-Id"),
    db: Session = Depends(get_db),
):
    """Cast or change vote for a debate (UPSERT)."""
    return await _handle_vote_upsert(payload, x_viewer_id, db)


@router.patch("", response_model=schemas.VoteResponse)
async def change_vote(
    payload: schemas.VoteCreate,
    x_viewer_id: Optional[str] = Header(None, alias="X-Viewer-Id"),
    db: Session = Depends(get_db),
):
    """Change vote for a debate (idempotent UPSERT)."""
    return await _handle_vote_upsert(payload, x_viewer_id, db)


@router.get("/{debate_id}", response_model=schemas.VoteCounts)
def get_votes(debate_id: int, db: Session = Depends(get_db)):
    """Get current aggregated vote counts and percentages."""
    counts = crud.get_vote_counts(db, debate_id)
    return schemas.VoteCounts(**counts)
