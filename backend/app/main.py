"""Application entrypoint.

    cd backend
    .venv/bin/python -m uvicorn app.main:app --port 8000

Open http://localhost:8000
"""

from .web.app import app

__all__ = ["app"]
