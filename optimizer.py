"""Talks to the LLM (Google Gemini) and returns an optimized prompt.

Provider-specific code (Gemini) is limited to _gemini_request() and
_friendly_error(). To switch provider later, change only those two.
"""

import re
import time

import config
from prompts import DEFAULT_LENGTH, EXPLANATION_MARKER, OPTIMIZED_MARKER, build_meta_prompt

NO_EXPLANATION_TEXT = "(The model did not give a separate explanation.)"


class OptimizerError(Exception):
    """Raised with a friendly message that the UI can show directly."""


def count_words(text: str) -> int:
    """Count words in a text (used for the word-count metrics)."""
    return len((text or "").split())


# ---------- Gemini-specific part ----------

def _gemini_request(system_instruction: str, user_text: str) -> str:
    """Make ONE Gemini call and return the reply text. May raise any SDK error."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=config.get_api_key(),
        http_options=types.HttpOptions(timeout=config.TIMEOUT_SECONDS * 1000),  # in ms
    )
    response = client.models.generate_content(
        model=config.get_model(),
        contents=user_text,
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )
    return response.text or ""


def _friendly_error(error: Exception) -> tuple[str, bool]:
    """Turn an API exception into (friendly message, is_temporary).

    is_temporary=True means a retry may help (server busy / timeout).
    """
    code = getattr(error, "code", None)  # HTTP status code on Gemini API errors
    text = str(error).lower()
    model = config.get_model()

    if code == 404:
        return (f"Model '{model}' was not found. Set a valid GEMINI_MODEL in your .env file.", False)
    if code == 429:
        return ("API quota or rate limit reached. Wait a minute and try again, "
                "or check your usage in Google AI Studio.", False)
    if code in (401, 403) or "api key" in text or "api_key" in text:
        return ("Your Gemini API key is invalid or not allowed. "
                "Check GEMINI_API_KEY in your .env file.", False)
    if "timeout" in type(error).__name__.lower() or "timed out" in text:
        return ("The request timed out. Please try again.", True)
    if isinstance(code, int) and code >= 500:
        return ("Gemini is temporarily busy or unavailable. Please try again shortly.", True)
    return (f"The Gemini API call failed ({type(error).__name__}). "
            "Check your internet connection and settings.", False)


def call_llm(system_instruction: str, user_text: str) -> str:
    """Call the LLM with retries on temporary errors. Returns reply text or raises OptimizerError."""
    if not config.get_api_key():
        raise OptimizerError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and add your key."
        )

    attempts = 1 + config.MAX_RETRIES
    for attempt in range(1, attempts + 1):
        try:
            text = _gemini_request(system_instruction, user_text)
        except Exception as e:  # any network / key / quota / model error
            message, temporary = _friendly_error(e)
            if temporary and attempt < attempts:
                time.sleep(config.RETRY_DELAY_SECONDS * attempt)  # wait a bit, then retry
                continue
            raise OptimizerError(message) from e
        if not text.strip():
            raise OptimizerError("The model returned an empty reply. Please try again.")
        return text
    raise OptimizerError("The Gemini API call failed.")  # not reachable; keeps function total


# ---------- Provider-independent part ----------

def _marker_pattern(marker: str) -> re.Pattern:
    """Regex matching a marker line loosely (any case, optional #/**/colon)."""
    words = marker.lstrip("# ").strip()
    return re.compile(rf"^[ \t]*#*[ \t]*\**[ \t]*{re.escape(words)}[ \t]*\**[ \t]*:?[ \t]*\**[ \t]*$",
                      re.IGNORECASE | re.MULTILINE)


def _strip_code_fence(text: str) -> str:
    """Remove one ``` fence wrapped around the whole text, if present."""
    text = text.strip()
    match = re.fullmatch(r"```[a-zA-Z]*\n(.*?)\n?```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def parse_reply(reply: str) -> tuple[str, str]:
    """Split the model reply into (optimized_prompt, explanation).

    Handles: both markers, only one marker, no markers (whole reply = optimized).
    """
    reply = (reply or "").strip()
    opt = _marker_pattern(OPTIMIZED_MARKER).search(reply)
    exp = _marker_pattern(EXPLANATION_MARKER).search(reply)

    if opt and exp and opt.start() < exp.start():
        optimized = reply[opt.end():exp.start()]
        explanation = reply[exp.end():]
    elif opt:  # no (valid) explanation section
        optimized = reply[opt.end():]
        explanation = ""
    elif exp:  # explanation only: text before it is the prompt
        optimized = reply[:exp.start()]
        explanation = reply[exp.end():]
    else:  # model ignored the format
        optimized, explanation = reply, ""

    optimized = _strip_code_fence(optimized) or reply
    return optimized, explanation.strip() or NO_EXPLANATION_TEXT


def optimize_prompt(rough_prompt: str, mode: str = "General",
                    length: str = DEFAULT_LENGTH, custom_instruction: str = "") -> tuple[str, str]:
    """Turn a rough prompt into (optimized_prompt, explanation). Raises OptimizerError."""
    rough_prompt = (rough_prompt or "").strip()
    custom_instruction = (custom_instruction or "").strip()
    if not rough_prompt:
        raise OptimizerError("Please enter a prompt first.")
    if len(rough_prompt) > config.MAX_INPUT_CHARS:
        raise OptimizerError(
            f"Your prompt is {len(rough_prompt)} characters long. "
            f"The limit is {config.MAX_INPUT_CHARS}. Please shorten it."
        )
    if len(custom_instruction) > config.MAX_CUSTOM_CHARS:
        raise OptimizerError(
            f"The custom instruction is too long (limit {config.MAX_CUSTOM_CHARS} characters)."
        )
    reply = call_llm(build_meta_prompt(mode, length, custom_instruction), rough_prompt)
    return parse_reply(reply)
