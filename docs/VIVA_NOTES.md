# Viva Notes: AI Prompt Optimizer

## 1. Objective
Many people write vague prompts ("write code for a todo app") and get weak answers from AI tools.
This project takes a rough prompt and automatically rewrites it into a clear, specific, structured
prompt, and explains what was improved. The goal is to show how prompt engineering can be automated
with an LLM, using only Python.

## 2. Architecture (one paragraph)
The user types a prompt in the **Streamlit** UI (`app.py`). `optimizer.py` checks the input, asks
`prompts.py` to build a *meta-prompt* (rules for rewriting + mode + length + optional custom
instruction) and sends it with the user's text to the **Gemini API**. Temporary errors are retried
at most twice. The reply, which has two marked sections, is parsed into the optimized prompt and an
explanation. The UI shows original and optimized side by side, and `storage.py` saves the result in
**SQLite** so it appears in the history sidebar (reload, delete, clear, export). `config.py` holds all
settings and reads secrets from `.env`.

## 3. What each file does
| File | Job |
|---|---|
| `app.py` | Streamlit UI: inputs, buttons, side-by-side output, metrics, history sidebar, export buttons |
| `optimizer.py` | `optimize_prompt()` (main function), validation, `call_llm()` with retries, friendly errors, `parse_reply()` |
| `prompts.py` | Meta-prompt text, mode focus, mode descriptions, length guides, `build_meta_prompt()` |
| `storage.py` | SQLite: create table, save, load last N, delete one, clear all, export CSV/JSON |
| `config.py` | Constants (limits, default model) and readers for `.env` values (key, model, DB path) |
| `test_core.py` | Unit tests with a mocked Gemini |
| `run.bat` / `run.sh` | Create venv, install requirements, create `.env`, start the app |
| `.streamlit/config.toml` | UI theme |

## 4. What is meta-prompting?
A *prompt* is an instruction to an AI. A *meta-prompt* is an instruction whose job is to produce or
improve another prompt. Here, our meta-prompt tells Gemini: "You are a prompt engineer. Rewrite the
user's rough prompt, keep the intent, add structure, don't answer it." The user's rough prompt is the
input; the improved prompt is the output.

## 5. How `prompts.py` works (example)
`build_meta_prompt(mode, length, custom_instruction)` joins four parts:
1. **Base rules**: rewrite, keep intent, use sections, use placeholders, do not answer, reply in a fixed format.
2. **Mode focus**: e.g. Coding says "specify language, inputs/outputs, edge cases".
3. **Length guide**: Short (~80 words), Balanced (100-200), Detailed (250+).
4. **Custom instruction** (only if the user typed one).

The fixed reply format uses two marker lines (`### OPTIMIZED PROMPT`, `### WHAT IMPROVED`), so
`parse_reply()` can split the answer easily.

Example (mode Coding, length Balanced):
- Input: `write code for a todo app`
- Output (typical, written by the model so wording varies):
  ```
  ### OPTIMIZED PROMPT
  Role: You are an experienced [language] developer.
  Task: Write a simple to-do app that lets a user add, complete and delete tasks.
  Requirements: Persist tasks; handle empty input; add brief comments.
  Output format: Full code, then a short explanation of how to run it.

  ### WHAT IMPROVED
  - Added a role and a clear task
  - Listed requirements and edge cases
  - Defined the output format
  ```

## 6. Why these technologies?
- **Streamlit**: build a web UI in pure Python in a few lines, no HTML/JS or separate backend.
- **Gemini (google-genai)**: has a free tier for students, fast Flash models, and a simple official Python SDK.
- **SQLite**: built into Python (no server to install), a single file, perfect for small local history.
- **python-dotenv / `.env`**: keeps the API key out of the code and out of Git.
- **unittest + mock**: built into Python; mocking lets us test without a real key or internet.

## 7. Fifteen likely viva questions
1. **What does your project do?** It rewrites a rough prompt into a clear, structured one using Gemini and explains the improvements.
2. **What is prompt engineering?** Writing prompts carefully (role, context, constraints, format) to get better AI output.
3. **What is meta-prompting?** A prompt that instructs the AI to create or improve another prompt (section 4).
4. **Why Streamlit?** Pure-Python UI, very fast to build, easy to run with `streamlit run app.py`.
5. **How does Streamlit work?** It re-runs the whole script on every interaction; `st.session_state` keeps values between runs.
6. **Why do you use `st.session_state`?** Because of reruns, otherwise the result and inputs would vanish after each click.
7. **How is the API key kept safe?** It is read from `.env` (via python-dotenv), `.env` is in `.gitignore`, and only `.env.example` with a placeholder is committed.
8. **Why is the model name in `.env`?** Google retires models over time; changing `GEMINI_MODEL` fixes it without editing code.
9. **How do you handle API errors?** `_friendly_error()` maps errors (404, 429, key problems, timeout, 5xx) to clear messages; the UI shows them with `st.error`, so the app never crashes.
10. **What is retrying and when do you do it?** Trying again after a failure. Only for temporary errors (server busy, timeout), max 2 retries with a short wait; not for wrong key or quota.
11. **How do you parse the model's reply?** Two marker headings split the text. If a marker is missing, fallbacks use the whole reply as the prompt, so something sensible is always shown.
12. **Why SQLite and how is the table designed?** Built-in and serverless. Table `history`: id, created_at, mode, original, optimized, explanation.
13. **Why `?` placeholders in SQL?** They are parameterised queries, which prevent SQL injection.
14. **How did you test without an API key?** `unittest.mock` replaces the Gemini function with fake replies or errors, so tests are fast and need no internet.
15. **Limitations and future work?** Needs internet/key and depends on the model's quality; future: more providers, favourites, prompt scoring, multi-user login (see README).

## 8. Honest note
The real Gemini call was not executed during development (no API key in the build sandbox). All other logic is covered by unit tests and a headless Streamlit run with Gemini mocked. Before the viva, run the app once with your own key to confirm it end to end.
