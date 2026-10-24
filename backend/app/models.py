"""SQLAlchemy 2.0 typed ORM models for all database tables."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Debate(Base):
    __tablename__ = "debates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(Text, nullable=False)
    model_a: Mapped[str] = mapped_column(Text, nullable=False, default="openai/gpt-oss-120b")
    model_b: Mapped[str] = mapped_column(Text, nullable=False, default="qwen/qwen3.8-27b")
    agent_a_name: Mapped[str] = mapped_column(Text, nullable=False, default="GPT-OSS")
    agent_b_name: Mapped[str] = mapped_column(Text, nullable=False, default="Qwen")
    duration_secs: Mapped[int] = mapped_column(Integer, default=300)
    status: Mapped[str] = mapped_column(Text, default="draft")
    creator_token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InviteLink(Base):
    __tablename__ = "invite_links"

    uuid: Mapped[str] = mapped_column(Text, primary_key=True)
    debate_id: Mapped[int] = mapped_column(Integer, ForeignKey("debates.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Viewer(Base):
    __tablename__ = "viewers"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    debate_id: Mapped[int] = mapped_column(Integer, ForeignKey("debates.id"), nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(Text, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True)


class DebateRound(Base):
    __tablename__ = "debate_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    debate_id: Mapped[int] = mapped_column(Integer, ForeignKey("debates.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[str] = mapped_column(Text, nullable=False)
    argument: Mapped[str] = mapped_column(Text, nullable=False, default="")
    citations: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    search_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("debate_id", "viewer_id", name="uq_debate_viewer"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    debate_id: Mapped[int] = mapped_column(Integer, ForeignKey("debates.id"), nullable=False)
    viewer_id: Mapped[str] = mapped_column(Text, ForeignKey("viewers.id"), nullable=False)
    vote: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
