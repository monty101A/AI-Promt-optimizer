# ✨ AI Prompt Optimizer

A small college project. You type a rough prompt, an LLM (Google Gemini) rewrites it into a
clear, specific, structured prompt, and the app shows the **original and optimized versions
side by side** with a short explanation of what improved and why.

Pure Python: the frontend is also Python ([Streamlit](https://streamlit.io)).

## Features
- Modes: General, Coding, Writing, Study (each has its own meta-prompt)
- Optimized prompt in a copy-friendly code block + "what improved and why"
- Original vs Optimized side by side
- History of the last 20 prompts in the sidebar (click to reload), stored in SQLite
- Friendly errors: empty input, missing API key, API failure (the app never crashes)

## Setup (Windows)
1. Install Python 3.10+ from python.org (tick "Add Python to PATH").
2. Open Command Prompt in the project folder and run:
   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
3. Open `.env` in Notepad and paste your key: `GEMINI_API_KEY=...`
   (optionally change `GEMINI_MODEL`, default `gemini-2.5-flash`).

## Getting a Gemini API key
1. Go to https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** and copy it into `.env`. The free tier is enough for this project.
3. Never share `.env` or commit it (it is in `.gitignore`).

## Run
```bat
streamlit run app.py
```
The browser opens at http://localhost:8501.

## Tests
```bat
python -m unittest -v
```
The tests mock the Gemini call, so no API key is needed.

## How it works (architecture)
```
app.py  ──►  optimizer.py  ──►  Gemini API
  │              │
  │              └── prompts.py   (meta-prompt for each mode)
  └──────────►  storage.py  ──►  history.db (SQLite)
```
- `app.py` – Streamlit UI: input, mode selector, side-by-side output, history sidebar.
- `optimizer.py` – `optimize_prompt()` validates input, builds the meta-prompt, calls
  `call_llm()` (the only Gemini-specific function; swap it to change provider) and
  splits the reply into *optimized prompt* and *explanation*. Errors become `OptimizerError`
  with a friendly message that the UI displays.
- `prompts.py` – instructions telling the LLM how to rewrite prompts, per mode, and the
  fixed reply format (two marked sections) that makes parsing simple.
- `storage.py` – saves every result to SQLite and loads the latest 20.
