"""
This file exists for backwards compatibility.
The actual FastAPI application is in backend/main.py
"""
from backend.main import app

__all__ = ["app"]
