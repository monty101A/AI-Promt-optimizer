"""Meta-prompts: instructions we give to the LLM so it rewrites the user's prompt.

Each mode has its own "focus" text. All modes share the same base
instructions and the same output format, so optimizer.py can parse the reply.
"""

# Section markers the LLM must use. optimizer.py splits the reply on these.
OPTIMIZED_MARKER = "### OPTIMIZED PROMPT"
EXPLANATION_MARKER = "### WHAT IMPROVED"

# Base instructions shared by every mode.
BASE_INSTRUCTIONS = f"""You are an expert prompt engineer.
The user will give you a rough prompt. Rewrite it into a clear, specific,
well-structured prompt that another AI model can follow easily.

Rules:
- Keep the user's original intent. Do not invent facts or requirements.
- Where details are missing, add sensible placeholders like [language] or [audience].
- Structure the prompt with short labeled sections (e.g. Role, Task, Context,
  Requirements, Output format).
- Do NOT answer the prompt yourself. Only rewrite it.

Reply in EXACTLY this format and nothing else:

{OPTIMIZED_MARKER}
<the rewritten prompt>

{EXPLANATION_MARKER}
<3-5 short bullet points: what you improved and why>
"""

# Extra focus per mode.
MODE_FOCUS = {
    "General": "Focus on clarity, a clear goal, relevant context and a defined output format.",
    "Coding": (
        "Focus on programming: specify the language/framework and versions, "
        "inputs and outputs, constraints, edge cases, error handling, and ask "
        "for code with brief comments plus a short explanation."
    ),
    "Writing": (
        "Focus on writing: specify the audience, tone, style, length, "
        "structure and any key points that must be included."
    ),
    "Study": (
        "Focus on learning: specify the topic and level of the learner, ask for "
        "step-by-step simple explanations, examples, analogies and a short quiz or summary."
    ),
}

MODES = list(MODE_FOCUS.keys())


def build_meta_prompt(mode: str) -> str:
    """Return the full system instruction for the given mode (falls back to General)."""
    focus = MODE_FOCUS.get(mode, MODE_FOCUS["General"])
    return f"{BASE_INSTRUCTIONS}\nMode: {mode}\n{focus}"
