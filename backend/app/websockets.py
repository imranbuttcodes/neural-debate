"""WebSocket connection manager for debate rooms."""

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by debate_id."""

    def __init__(self):
        # debate_id → {viewer_id: WebSocket}
        self.active: dict[int, dict[str, WebSocket]] = {}

    async def connect(self, debate_id: int, viewer_id: str, ws: WebSocket):
        await ws.accept()
        if debate_id not in self.active:
            self.active[debate_id] = {}
        self.active[debate_id][viewer_id] = ws

    def disconnect(self, debate_id: int, viewer_id: str):
        if debate_id in self.active:
            self.active[debate_id].pop(viewer_id, None)
            if not self.active[debate_id]:
                del self.active[debate_id]

    def viewer_count(self, debate_id: int) -> int:
        return len(self.active.get(debate_id, {}))

    async def broadcast(self, debate_id: int, message: dict):
        """Send a JSON message to ALL viewers in a debate room."""
        conns = self.active.get(debate_id, {})
        dead = []
        for viewer_id, ws in conns.items():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(viewer_id)
        # Clean up dead connections
        for vid in dead:
            self.disconnect(debate_id, vid)

    async def send_personal(self, debate_id: int, viewer_id: str,
                            message: dict):
        """Send a JSON message to a single viewer."""
        conns = self.active.get(debate_id, {})
        ws = conns.get(viewer_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(debate_id, viewer_id)


# Singleton instance used across the app
ws_manager = ConnectionManager()
