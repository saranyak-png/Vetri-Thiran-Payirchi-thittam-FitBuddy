"""
FitBuddy – AI Fitness Plan Generator
database.py: SQLite database engine, session factory, and CRUD helpers.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'fitbuddy.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependency – yields a DB session and closes it afterwards
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------
def save_user(db, user_id: str, username: str, age: int, weight: float,
              goal: str, intensity: str):
    """Insert or update a user record by user_id."""
    from app.models import User  # local import to avoid circular imports

    existing = db.query(User).filter(User.user_id == user_id).first()
    if existing:
        # Update profile fields in case they changed since last submission
        existing.username = username
        existing.age = age
        existing.weight = weight
        existing.goal = goal
        existing.intensity = intensity
        db.commit()
        db.refresh(existing)
        return existing

    new_user = User(
        user_id=user_id,
        username=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def save_plan(db, user_id: str, original_plan: str, nutrition_tip: str):
    """Insert a new workout plan for the given user_id."""
    from app.models import WorkoutPlan

    plan = WorkoutPlan(
        user_id=user_id,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_original_plan(db, user_id: str) -> str | None:
    """Return the original workout plan text for a user, or None."""
    from app.models import WorkoutPlan

    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
    return plan.original_plan if plan else None


def update_plan(db, user_id: str, updated_plan: str):
    """Persist the AI-revised plan for an existing user."""
    from app.models import WorkoutPlan

    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
    if plan:
        plan.updated_plan = updated_plan
        db.commit()
        db.refresh(plan)
    return plan


def get_user(db, user_id: str):
    """Fetch a single user by user_id."""
    from app.models import User

    return db.query(User).filter(User.user_id == user_id).first()


def get_all_users(db):
    """Return all user records."""
    from app.models import User

    return db.query(User).all()


def get_all_plans(db):
    """Return all workout plan records."""
    from app.models import WorkoutPlan

    return db.query(WorkoutPlan).all()
