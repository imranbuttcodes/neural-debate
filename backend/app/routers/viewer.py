"""Viewer router: register viewers and list online viewers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db

router = APIRouter(prefix="/api/viewers", tags=["viewers"])


@router.post("", response_model=schemas.ViewerResponse)
def register_viewer(payload: schemas.ViewerCreate, db: Session = Depends(get_db)):
    """Register viewer (name + emoji avatar) returning a unique viewer_id."""
    debate = crud.get_debate(db, payload.debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")

    viewer = crud.create_viewer(
        db=db,
        debate_id=payload.debate_id,
        display_name=payload.display_name.strip() or "Anonymous",
        avatar_emoji=payload.avatar_emoji or "🎭",
    )

    return schemas.ViewerResponse(
        viewer_id=viewer.id,
        debate_id=viewer.debate_id,
        display_name=viewer.display_name,
        avatar_emoji=viewer.avatar_emoji,
    )


@router.get("/debate/{debate_id}")
def get_debate_viewers(debate_id: int, db: Session = Depends(get_db)):
    """List currently online viewers for a debate room."""
    viewers = crud.get_viewers(db, debate_id)
    return [
        {
            "id": v.id,
            "display_name": v.display_name,
            "avatar_emoji": v.avatar_emoji,
            "joined_at": v.joined_at.isoformat() if v.joined_at else None,
        }
        for v in viewers
    ]
