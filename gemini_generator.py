"""
FitBuddy – AI Fitness Plan Generator
gemini_generator.py: Generates a personalized 7-day workout plan
using the google-genai SDK, with automatic model fallback.
"""

import logging
import os
import time

from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

# Models tried in order; stable aliases first, then specific versions as fallback.
# On 503 (overloaded) each model is retried up to _MAX_RETRIES times before moving on.
# On 404 (not found / deprecated) the model is skipped immediately.
_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-lite-latest",
]

_MAX_RETRIES = 3        # retries per model on 503
_RETRY_DELAY = 2.0      # seconds between retries

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Return the shared Gemini client, raising ValueError if the key is absent."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. "
                "Add it to your .env file and restart the server."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _generate_with_fallback(prompt: str) -> str:
    """Try each model in _MODELS with retries on 503; skip on 404/429."""
    client = _get_client()
    last_exc: Exception | None = None
    for model in _MODELS:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return (response.text or "").strip()
            except (genai_errors.ClientError, genai_errors.ServerError) as exc:
                code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if code in (404, 429):
                    # 404 = model not found; 429 = quota exhausted for this model
                    logger.warning("Model %s skipped (%s), trying next.", model, code)
                    last_exc = exc
                    break  # skip to next model immediately
                if code == 503:
                    last_exc = exc
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Model %s overloaded (503), retry %d/%d in %.0fs.",
                            model, attempt, _MAX_RETRIES, _RETRY_DELAY,
                        )
                        time.sleep(_RETRY_DELAY)
                        continue
                    logger.warning("Model %s overloaded after %d retries, trying next.", model, _MAX_RETRIES)
                    break  # move to next model
                raise
    raise last_exc  # all models exhausted


def generate_workout_gemini(
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> str:
    """Return a formatted 7-day personalised workout plan from Gemini 2.0 Flash.

    Args:
        username:  Display name of the user.
        age:       Age in years (must be 10–120).
        weight:    Body weight in kg (must be > 0).
        goal:      Fitness goal (e.g. "weight loss", "muscle gain").
        intensity: Workout intensity level (e.g. "low", "medium", "high").

    Returns:
        A plain-text plan string, or a user-facing error message prefixed with
        an emoji indicator so callers can distinguish success from failure.
    """
    # --- input validation -----------------------------------------------
    if not username or not username.strip():
        return "⚠️  Username must not be empty."
    if not (10 <= age <= 120):
        return f"⚠️  Age {age} is out of the valid range (10–120)."
    if weight <= 0:
        return f"⚠️  Weight {weight} kg is not valid."
    if not goal or not goal.strip():
        return "⚠️  Fitness goal must not be empty."
    if not intensity or not intensity.strip():
        return "⚠️  Intensity level must not be empty."

    prompt = f"""
You are an expert personal fitness trainer. Create a detailed, personalized 7-day workout plan
for the following individual:

- Name: {username}
- Age: {age} years
- Weight: {weight} kg
- Fitness Goal: {goal}
- Workout Intensity: {intensity}

Format the plan exactly as follows for each day:

DAY X – [Focus Area]
─────────────────────────────────
🔥 Warm-Up (5–10 minutes)
  • [Exercise 1]
  • [Exercise 2]

💪 Main Workout
  • [Exercise] – [Sets] × [Reps/Duration] | Rest: [time]
  (list 4–6 exercises)

🧊 Cool-Down / Recovery Tip
  • [Tip or stretch]

Repeat this structure for all 7 days.
Tailor intensity, exercise selection, and volume strictly to the user's goal and intensity level.
Provide only the plan — no introduction or closing remarks.
""".strip()

    try:
        plan = _generate_with_fallback(prompt)
        if not plan:
            logger.warning("Gemini returned an empty response for user %r", username)
            return "⚠️  Gemini returned an empty response. Please try again."
        return plan
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        return f"⚠️  Configuration error: {exc}"
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error generating workout for user %r", username)
        return f"❌ Unexpected error: {exc}"
