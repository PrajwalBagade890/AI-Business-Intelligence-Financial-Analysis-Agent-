"""Vercel Serverless Function entrypoint for FastAPI backend."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

# Vercel ASGI handler
handler = app
