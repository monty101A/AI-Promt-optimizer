# ✨ AI Prompt Optimizer

A college project. You type a rough prompt, an LLM (Google Gemini) rewrites it into a clear,
specific, structured prompt, and the app shows the **original and optimized versions side by
side** with a short explanation of what improved and why.

Pure Python: the frontend is also Python ([Streamlit](https://streamlit.io)).

## Features
- Modes: General, Coding, Writing, Study (each with a one-line description in the UI)
- Output length: Short / Balanced / Detailed
- Optional custom instruction (e.g. "Hinglish mein output", "keep it short")
- Side-by-side Original vs Optimized, word-count metrics, copy button on the code block
- **Optimize again**: feed the optimized prompt back in and improve it once more
- History (last 20) in the sidebar: reload, delete one entry, clear all (with confirmation),
  export everything as CSV or JSON
- Input validation (empty, over 4000 characters) and friendly errors for a missing/invalid API
  key, unknown model, quota limit, timeout and server errors. Temporary errors are retried (max 2).

## Setup (Windows)
Easiest: install Python 3.10+ from python.org (tick "Add Python to PATH"), then double-click
**`run.bat`**. It creates the virtual environment, installs the packages, creates `.env` and
starts the app. On the first run it opens `.env` in Notepad: paste your key, save, run again.

Manual steps (same thing):
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
Open `.env` and set `GEMINI_API_KEY=...`. Mac/Linux: use `./run.sh`.

## Getting a Gemini API key
1. Go to https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** and copy it into `.env`. The free tier is enough for this project.
3. Never share `.env` or commit it (it is in `.gitignore`).

`.env` settings: `GEMINI_API_KEY` (required), `GEMINI_MODEL` (default `gemini-3.8-flash`),
`DB_PATH` (default `history.db`). If you get "model not found", pick a current model name from
https://ai.google.dev/gemini-api/docs/models and put it in `GEMINI_MODEL`.

## Run
```bat
streamlit run app.py
```
The browser opens at http://localhost:8501.

## Tests
```bat
python -m unittest -v
```
The Gemini call is always mocked, so no API key or internet is needed for the tests.

## Project structure
```
app.py            Streamlit UI (inputs, results, history sidebar)
optimizer.py      Validation, Gemini call + retries, error messages, reply parsing
prompts.py        Meta-prompts: modes, lengths, custom instruction
storage.py        SQLite history: save, load, delete, clear, CSV/JSON export
config.py         All settings and limits in one place (reads .env)
test_core.py      Unit tests (Gemini mocked)
run.bat / run.sh  One-click launchers
.streamlit/       Theme (config.toml)
docs/VIVA_NOTES.md  Notes for the viva
```

## Architecture
```
User -> Streamlit (app.py) -> optimizer.py -> Gemini API
                                   |
                              parse reply -> SQLite (storage.py) -> history sidebar
```
1. The user enters a prompt, picks mode/length and an optional instruction in `app.py`.
2. `optimizer.optimize_prompt()` validates the input and asks `prompts.py` for the meta-prompt.
3. `call_llm()` sends it to Gemini (retrying temporary errors) and returns the reply text.
4. `parse_reply()` splits the reply into *optimized prompt* and *explanation*.
5. `app.py` shows the result and `storage.py` saves it to SQLite.

## Limitations
- Needs internet and a Gemini API key; free-tier quotas apply.
- Quality depends on the model; the output is a suggestion, not a guarantee.
- History is stored locally in one SQLite file, with no user accounts.
- Mode, length and custom instruction are not stored in history (only mode, original, optimized, explanation).
- The real Gemini call was not run during development in the sandbox (tests use a mock).

## Future scope
- Support more providers (OpenAI, Claude, local models) by replacing the two Gemini functions in `optimizer.py`
- Save/load custom meta-prompts and favourites
- Compare outputs of several models, or score prompt quality
- Multi-user login and a hosted deployment
