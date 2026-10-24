"""FastAPI application entrypoint with CORS, routers, and WebSocket room management."""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Load environment variables before initializing DB & agents
load_dotenv()

from . import crud, models
from .db import Base, SessionLocal, engine, get_db
from .routers import debate, viewer, vote
from .websockets import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")
    yield


app = FastAPI(
    title="AI Debate Arena API",
    version="2.0.0",
    description="Real-time multi-agent debate platform powered by Groq and audience voting",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST routers
app.include_router(debate.router)
app.include_router(viewer.router)
app.include_router(vote.router)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "app": "AI Debate Arena",
        "version": "2.0.0",
    }


@app.websocket("/ws/debates/{debate_id}")
async def debate_websocket_endpoint(
    websocket: WebSocket,
    debate_id: int,
    viewer_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for debate rooms.
    Fans out live streaming tokens, timer ticks, voting events, and state snapshots.
    """
    actual_viewer_id = viewer_id or f"anon_{id(websocket)}"
    await ws_manager.connect(debate_id, actual_viewer_id, websocket)

    db: Session = SessionLocal()
    viewer_obj = None

    try:
        # Mark viewer as online & notify room
        if viewer_id:
            viewer_obj = crud.get_viewer(db, viewer_id)
            if viewer_obj:
                crud.set_viewer_online(db, viewer_id, True)
                await ws_manager.broadcast(
                    debate_id,
                    {
                        "type": "viewer_joined",
                        "viewer_id": viewer_obj.id,
                        "name": viewer_obj.display_name,
                        "avatar": viewer_obj.avatar_emoji,
                        "total_viewers": ws_manager.viewer_count(debate_id),
                    },
                )

        # Send full initial state snapshot to the connecting client
        debate_obj = crud.get_debate(db, debate_id)
        if debate_obj:
            from .routers.debate import get_debate_state
            snapshot = get_debate_state(debate_id=debate_id, viewer_id=viewer_id, db=db)
            await websocket.send_text(json.dumps(snapshot))

        # Listen for client messages (e.g., ping/pong or heartbeats)
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
    finally:
        ws_manager.disconnect(debate_id, actual_viewer_id)
        if viewer_obj:
            try:
                crud.set_viewer_online(db, viewer_obj.id, False)
                await ws_manager.broadcast(
                    debate_id,
                    {
                        "type": "viewer_left",
                        "name": viewer_obj.display_name,
                        "avatar": viewer_obj.avatar_emoji,
                        "total_viewers": ws_manager.viewer_count(debate_id),
                    },
                )
            except Exception as e:
                logger.error(f"Error handling viewer disconnect: {e}")
        db.close()
