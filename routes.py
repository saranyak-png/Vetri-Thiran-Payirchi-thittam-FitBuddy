"""
FitBuddy – AI Fitness Plan Generator
routes.py: All FastAPI route handlers – the operational core of FitBuddy.
Bridges the Jinja2 frontend, Gemini AI modules, and the SQLite database.
"""

import os
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import (
    get_db,
    save_user,
    save_plan,
    get_original_plan,
    update_plan,
    get_user,
    get_all_users,
    get_all_plans,
)
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan

# ---------------------------------------------------------------------------
# Template directory resolution (works regardless of working directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helper – builds the shared result.html template context
# ---------------------------------------------------------------------------
def _build_result_context(
    *,
    username: str,
    user_id: str,
    age,
    weight,
    goal,
    intensity,
    workout_plan,
    nutrition_tip,
    updated_plan,
    feedback_message: str | None,
) -> dict:
    return {
        "username": username,
        "user_id": user_id,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity,
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip,
        "updated_plan": updated_plan,
        "feedback_message": feedback_message,
    }


# ---------------------------------------------------------------------------
# GET  /  – Home page: display the user input form
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


# ---------------------------------------------------------------------------
# POST  /generate-workout  – Generate personalized 7-day plan + nutrition tip
# ---------------------------------------------------------------------------
@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1. Generate workout plan via Gemini 2.0 Flash
    workout_plan = generate_workout_gemini(
        username=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )

    # 2. Generate nutrition tip via Gemini Flash
    nutrition_tip = generate_nutrition_tip_with_flash(goal=goal)

    # 3. Persist user and plan to SQLite
    save_user(
        db=db,
        user_id=user_id,
        username=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )
    save_plan(
        db=db,
        user_id=user_id,
        original_plan=workout_plan,
        nutrition_tip=nutrition_tip,
    )

    return templates.TemplateResponse(
        request,
        "result.html",
        _build_result_context(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
            workout_plan=workout_plan,
            nutrition_tip=nutrition_tip,
            updated_plan=None,
            feedback_message=None,
        ),
    )


# ---------------------------------------------------------------------------
# POST  /submit-feedback  – Update the plan based on user feedback
# ---------------------------------------------------------------------------
@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1. Retrieve user details and original plan from DB
    user = get_user(db=db, user_id=user_id)
    original_plan = get_original_plan(db=db, user_id=user_id)

    if not user or not original_plan:
        return templates.TemplateResponse(
            request,
            "result.html",
            _build_result_context(
                username="Unknown",
                user_id=user_id,
                age="–",
                weight="–",
                goal="–",
                intensity="–",
                workout_plan=None,
                nutrition_tip=None,
                updated_plan=None,
                feedback_message=(
                    f"⚠️  No plan found for User ID '{user_id}'. "
                    "Please generate a plan first."
                ),
            ),
        )

    # 2. Use Gemini 2.0 Flash to revise the plan
    try:
        revised_plan = update_workout_plan(
            original_plan=original_plan,
            feedback=feedback,
        )
    except (ValueError, RuntimeError, Exception) as exc:
        return templates.TemplateResponse(
            request,
            "result.html",
            _build_result_context(
                username=str(user.username),
                user_id=str(user.user_id),
                age=user.age,
                weight=user.weight,
                goal=user.goal,
                intensity=user.intensity,
                workout_plan=original_plan,
                nutrition_tip=None,
                updated_plan=None,
                feedback_message=f"❌ Could not update plan: {exc}",
            ),
        )

    # 3. Generate a fresh nutrition tip for the updated plan
    new_nutrition_tip = generate_nutrition_tip_with_flash(goal=str(user.goal))

    # 4. Save the updated plan to the database
    update_plan(db=db, user_id=user_id, updated_plan=revised_plan)

    return templates.TemplateResponse(
        request,
        "result.html",
        _build_result_context(
            username=str(user.username),
            user_id=str(user.user_id),
            age=user.age,
            weight=user.weight,
            goal=user.goal,
            intensity=user.intensity,
            workout_plan=original_plan,
            nutrition_tip=new_nutrition_tip,
            updated_plan=revised_plan,
            feedback_message="✅ Your workout plan has been updated based on your feedback!",
        ),
    )


# ---------------------------------------------------------------------------
# GET  /view-all-users  – Admin dashboard showing all users and their plans
# ---------------------------------------------------------------------------
@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(request: Request, db: Session = Depends(get_db)):
    users = get_all_users(db=db)
    plans = get_all_plans(db=db)

    # Build a lookup dict: user_id → plan record
    plans_by_user = {plan.user_id: plan for plan in plans}

    return templates.TemplateResponse(
        request,
        "all_users.html",
        {
            "users": users,
            "plans_by_user": plans_by_user,
        },
    )
