"""All database CRUD operations, including vote UPSERT."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from . import models


def _utcnow():
    return datetime.now(timezone.utc)


# ── Debate ─────────────────────────────────────────────────────────

def create_debate(db: Session, topic: str, description: str, tone: str,
                  duration_secs: int) -> tuple[models.Debate, models.InviteLink]:
    """Create a debate and its invite link. Returns (debate, invite_link)."""
    creator_token = str(uuid.uuid4())
    debate = models.Debate(
        topic=topic,
        description=description,
        tone=tone,
        duration_secs=min(duration_secs, 300),  # Cap at 5 min
        creator_token=creator_token,
    )
    db.add(debate)
    db.flush()  # Get the debate.id

    invite = models.InviteLink(
        uuid=uuid.uuid4().hex,
        debate_id=debate.id,
        expires_at=_utcnow() + timedelta(hours=24),
    )
    db.add(invite)
    db.commit()
    db.refresh(debate)
    db.refresh(invite)
    return debate, invite


def get_debate(db: Session, debate_id: int) -> models.Debate | None:
    return db.query(models.Debate).filter(models.Debate.id == debate_id).first()


def get_debate_by_invite(db: Session, invite_uuid: str) -> models.Debate | None:
    invite = db.query(models.InviteLink).filter(
        models.InviteLink.uuid == invite_uuid
    ).first()
    if not invite:
        return None
    return get_debate(db, invite.debate_id)


def start_debate(db: Session, debate: models.Debate) -> models.Debate:
    now = _utcnow()
    debate.status = "running"
    debate.starts_at = now
    debate.ends_at = now + timedelta(seconds=debate.duration_secs)
    db.commit()
    db.refresh(debate)
    return debate


def finish_debate(db: Session, debate_id: int, winner: str):
    debate = get_debate(db, debate_id)
    if debate:
        debate.status = "finished"
        debate.winner = winner
        db.commit()


# ── Viewer ─────────────────────────────────────────────────────────

def create_viewer(db: Session, debate_id: int, display_name: str,
                  avatar_emoji: str) -> models.Viewer:
    viewer = models.Viewer(
        id=str(uuid.uuid4()),
        debate_id=debate_id,
        display_name=display_name,
        avatar_emoji=avatar_emoji,
    )
    db.add(viewer)
    db.commit()
    db.refresh(viewer)
    return viewer


def get_viewer(db: Session, viewer_id: str) -> models.Viewer | None:
    return db.query(models.Viewer).filter(models.Viewer.id == viewer_id).first()


def get_viewers(db: Session, debate_id: int) -> list[models.Viewer]:
    return db.query(models.Viewer).filter(
        models.Viewer.debate_id == debate_id,
        models.Viewer.is_online == True,
    ).all()


def set_viewer_online(db: Session, viewer_id: str, online: bool):
    viewer = get_viewer(db, viewer_id)
    if viewer:
        viewer.is_online = online
        viewer.last_seen_at = _utcnow()
        db.commit()


# ── Rounds ─────────────────────────────────────────────────────────

def create_round(db: Session, debate_id: int, round_number: int,
                 label: str, agent: str, model_name: str,
                 search_query: str = "") -> models.DebateRound:
    rnd = models.DebateRound(
        debate_id=debate_id,
        round_number=round_number,
        label=label,
        agent=agent,
        model_name=model_name,
        search_query=search_query,
    )
    db.add(rnd)
    db.commit()
    db.refresh(rnd)
    return rnd


def update_round(db: Session, round_id: int, argument: str,
                 citations: list | None = None):
    rnd = db.query(models.DebateRound).filter(
        models.DebateRound.id == round_id
    ).first()
    if rnd:
        rnd.argument = argument
        rnd.citations = citations or []
        rnd.ended_at = _utcnow()
        db.commit()


def get_rounds(db: Session, debate_id: int) -> list[models.DebateRound]:
    return db.query(models.DebateRound).filter(
        models.DebateRound.debate_id == debate_id
    ).order_by(models.DebateRound.round_number).all()


# ── Votes (UPSERT) ────────────────────────────────────────────────

def upsert_vote(db: Session, debate_id: int, viewer_id: str,
                vote: str) -> bool:
    """Insert or update a vote. Returns True if vote changed."""
    existing = db.query(models.Vote).filter_by(
        debate_id=debate_id, viewer_id=viewer_id
    ).first()

    if existing:
        if existing.vote == vote:
            return False  # No change
        existing.vote = vote
        existing.updated_at = _utcnow()
    else:
        db.add(models.Vote(
            debate_id=debate_id,
            viewer_id=viewer_id,
            vote=vote,
        ))
    db.commit()
    return True


def get_vote_counts(db: Session, debate_id: int) -> dict:
    """Returns {A, B, total, percent_A, percent_B}."""
    votes = db.query(models.Vote).filter_by(debate_id=debate_id).all()
    a = sum(1 for v in votes if v.vote == "A")
    b = sum(1 for v in votes if v.vote == "B")
    total = a + b
    return {
        "A": a,
        "B": b,
        "total": total,
        "percent_A": round((a / total * 100), 1) if total > 0 else 0.0,
        "percent_B": round((b / total * 100), 1) if total > 0 else 0.0,
    }


def get_viewer_vote(db: Session, debate_id: int,
                    viewer_id: str) -> str | None:
    """Returns 'A', 'B', or None if viewer hasn't voted."""
    vote = db.query(models.Vote).filter_by(
        debate_id=debate_id, viewer_id=viewer_id
    ).first()
    return vote.vote if vote else None
