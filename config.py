"""All settings in one place (no magic strings elsewhere).

Secrets and choices come from the .env file; fixed limits are constants here.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads the .env file into environment variables

# ---- Defaults (used when .env does not override them) ----
DEFAULT_MODEL = "gemini-3.8-flash"  # fast Flash model; change in .env via GEMINI_MODEL
DEFAULT_DB_PATH = "history.db"

# ---- Fixed limits ----
MAX_INPUT_CHARS = 4000      # longest rough prompt we accept
MAX_CUSTOM_CHARS = 500      # longest custom instruction we accept
HISTORY_LIMIT = 20          # entries shown in the sidebar
MAX_RETRIES = 2             # extra attempts after a temporary API error
RETRY_DELAY_SECONDS = 1     # wait before retry n = n * this value
TIMEOUT_SECONDS = 30        # give up on one API call after this long

# Placeholder text from .env.example that is NOT a real key.
PLACEHOLDER_KEY = "your_api_key_here"


def get_api_key() -> str:
    """Return the Gemini API key from .env (empty string if missing or placeholder)."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return "" if key == PLACEHOLDER_KEY else key


def get_model() -> str:
    """Return the model name from .env, or the default."""
    return os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL


def get_db_path() -> str:
    """Return the SQLite file path from .env (DB_PATH), or the default."""
    return os.getenv("DB_PATH", "").strip() or DEFAULT_DB_PATH
