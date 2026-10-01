"""
FitBuddy – AI Fitness Plan Generator
schemas.py: Pydantic models for request validation.
"""

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """User profile submitted from the homepage form."""
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    username: str = Field(..., min_length=1, description="User's display name")
    age: int = Field(..., ge=5, le=120, description="Age in years")
    weight: float = Field(..., gt=0, description="Body weight in kilograms")
    goal: str = Field(..., description="Fitness goal (e.g., weight loss, muscle gain)")
    intensity: str = Field(..., description="Workout intensity: low | medium | high")


class FeedbackRequest(BaseModel):
    """Feedback submitted by the user to refine their plan."""
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    feedback: str = Field(..., min_length=5, description="User's feedback on the plan")
