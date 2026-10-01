"""
FitBuddy – AI Fitness Plan Generator
gemini_flash_generator.py: Generates a concise nutrition / recovery tip
using the google-genai SDK, with automatic model fallback.
"""

import logging
import os
import textwrap
import time

from google import genai
from google.genai import errors as genai_errors

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

_log = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
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


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Use Gemini to generate a concise, practical nutrition or recovery tip
    tailored to the user's fitness goal.

    Returns a plain-text tip string, or an error message if the call fails.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return (
            "⚠️  GOOGLE_API_KEY is not configured.\n"
            "Please add your Gemini API key to the .env file and restart the server."
        )

    prompt = textwrap.dedent(f"""
        You are a certified nutritionist and fitness recovery specialist.
        Provide ONE concise, practical nutrition or recovery tip (3–5 sentences) for someone
        whose fitness goal is: "{goal}".

        Focus on:
        - Specific foods, macros, or hydration advice
        - Recovery strategies (sleep, stretching, active rest)
        - Why this tip is important for their goal

        Be direct and actionable. No bullet lists — write as a short paragraph.
    """).strip()

    try:
        return _generate_with_fallback(prompt)
    except Exception as exc:
        _log.error("Gemini API error: %s", exc)
        return f"❌ Gemini API error: {exc}"
