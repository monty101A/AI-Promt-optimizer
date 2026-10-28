"""Talks to the LLM (Google Gemini) and returns an optimized prompt.

All provider-specific code lives in call_llm(). To switch to another
provider later, only that one function needs to change.
"""

import os

from dotenv import load_dotenv

from prompts import EXPLANATION_MARKER, OPTIMIZED_MARKER, build_meta_prompt

load_dotenv()  # reads GEMINI_API_KEY / GEMINI_MODEL from the .env file

DEFAULT_MODEL = "gemini-2.5-flash"


class OptimizerError(Exception):
    """Raised with a friendly message that the UI can show directly."""


def call_llm(system_instruction: str, user_text: str) -> str:
    """Send one request to Gemini and return the reply text. (Provider-specific part.)"""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        raise OptimizerError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=user_text,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )
        text = response.text
    except Exception as e:  # any network / key / quota / model error
        raise OptimizerError(
            f"The Gemini API call failed ({type(e).__name__}). "
            "Check your API key, model name (GEMINI_MODEL) and internet connection."
        ) from e

    if not text:
        raise OptimizerError("The model returned an empty reply. Please try again.")
    return text


def parse_reply(reply: str) -> tuple[str, str]:
    """Split the model reply into (optimized_prompt, explanation)."""
    if OPTIMIZED_MARKER in reply:
        after = reply.split(OPTIMIZED_MARKER, 1)[1]
        optimized, _, explanation = after.partition(EXPLANATION_MARKER)
        return optimized.strip(), explanation.strip()
    # Model ignored the format: show everything as the optimized prompt.
    return reply.strip(), "(The model did not give a separate explanation.)"


def optimize_prompt(rough_prompt: str, mode: str = "General") -> tuple[str, str]:
    """Turn a rough prompt into (optimized_prompt, explanation). Raises OptimizerError."""
    rough_prompt = (rough_prompt or "").strip()
    if not rough_prompt:
        raise OptimizerError("Please enter a prompt first.")
    reply = call_llm(build_meta_prompt(mode), rough_prompt)
    return parse_reply(reply)
