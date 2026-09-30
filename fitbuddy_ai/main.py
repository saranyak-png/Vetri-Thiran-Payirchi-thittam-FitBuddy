"""
FitBuddy – AI Fitness Plan Generator
main.py: Application entry point. Creates the FastAPI app, mounts static
files, initialises the database, and includes the router.
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv()

from app.database import engine, Base
from app.routes import router
import app.models  # noqa: F401 – ensure models are registered with Base

# ---------------------------------------------------------------------------
# Create all database tables (idempotent – safe to run every startup)
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description=(
        "A web application that uses Google Gemini AI to generate personalized "
        "7-day workout plans and nutrition tips based on your fitness goals."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Static files (CSS, images)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---------------------------------------------------------------------------
# Register all routes
# ---------------------------------------------------------------------------
app.include_router(router)
