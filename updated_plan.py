"""
FitBuddy – AI Fitness Plan Generator
updated_plan.py: Revises an existing workout plan using the google-genai SDK
based on the user's text feedback, with automatic model fallback.
"""

import logging
import os
import time

from google import genai
from google.genai import errors as genai_errors

_log = logging.getLogger(__name__)

_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-lite-latest",
]

_MAX_RETRIES = 3
_RETRY_DELAY = 2.0

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Add your Gemini API key to the .env file and restart the server."
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
                    _log.warning("Model %s skipped (%s), trying next.", model, code)
                    last_exc = exc
                    break
                if code == 503:
                    last_exc = exc
                    if attempt < _MAX_RETRIES:
                        _log.warning(
                            "Model %s overloaded (503), retry %d/%d in %.0fs.",
                            model, attempt, _MAX_RETRIES, _RETRY_DELAY,
                        )
                        time.sleep(_RETRY_DELAY)
                        continue
                    _log.warning("Model %s overloaded after %d retries, trying next.", model, _MAX_RETRIES)
                    break
                raise
    raise last_exc  # all models exhausted


_PROMPT_TEMPLATE = """\
You are an expert personal fitness trainer reviewing a client's workout plan.
The client has provided feedback and you must update the plan accordingly.

ORIGINAL 7-DAY WORKOUT PLAN:
{original_plan}

CLIENT FEEDBACK:
{feedback}

Instructions:
1. Keep the same 7-day structure.
2. Incorporate ALL of the client's feedback directly into the plan.
3. Maintain the same formatting style as the original plan:
   - DAY X – [Focus Area]
   - 🔥 Warm-Up, 💪 Main Workout, 🧊 Cool-Down sections
4. Do NOT add any introduction or closing remarks.
5. Return ONLY the updated 7-day plan.\
"""


def update_workout_plan(original_plan: str, feedback: str) -> str:
    """Revise an existing workout plan using Gemini with automatic model fallback.

    Args:
        original_plan: Full text of the previously generated 7-day plan.
        feedback: Free-text feedback from the user (e.g. "add more cardio").

    Returns:
        Revised 7-day plan as plain text.

    Raises:
        ValueError: If the API key is not configured.
        RuntimeError: If all models return an empty response.
    """
    prompt = _PROMPT_TEMPLATE.format(
        original_plan=original_plan.strip(),
        feedback=feedback.strip(),
    )
    revised = _generate_with_fallback(prompt)
    if not revised:
        raise RuntimeError("Gemini returned an empty response for the plan update.")
    return revised
