"""Meta-prompts: instructions we give to the LLM so it rewrites the user's prompt.

Meta-prompting = writing a prompt whose job is to produce/improve another prompt.
The final instruction is built from: base rules + mode focus + length + custom note.
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

# One-line description of each mode, shown in the UI.
MODE_DESCRIPTIONS = {
    "General": "Everyday prompts: adds a clear goal, context and output format.",
    "Coding": "Programming tasks: adds language, inputs/outputs, edge cases and tests.",
    "Writing": "Essays, emails, posts: adds audience, tone, style and length.",
    "Study": "Learning help: asks for simple steps, examples and a short quiz.",
}

MODES = list(MODE_FOCUS.keys())

# How long the OPTIMIZED PROMPT should be.
LENGTH_GUIDE = {
    "Short": "Keep the optimized prompt short: at most about 80 words, only the essentials.",
    "Balanced": "Make the optimized prompt moderately detailed: about 100-200 words.",
    "Detailed": "Make the optimized prompt thorough and detailed: 250 words or more, with examples if useful.",
}

LENGTHS = list(LENGTH_GUIDE.keys())
DEFAULT_LENGTH = "Balanced"


def build_meta_prompt(mode: str, length: str = DEFAULT_LENGTH, custom_instruction: str = "") -> str:
    """Build the full system instruction.

    Unknown mode/length fall back to General/Balanced. A non-empty
    custom_instruction is appended as an extra requirement for the rewritten prompt.
    """
    focus = MODE_FOCUS.get(mode, MODE_FOCUS["General"])
    length_text = LENGTH_GUIDE.get(length, LENGTH_GUIDE[DEFAULT_LENGTH])
    text = f"{BASE_INSTRUCTIONS}\nMode: {mode}\n{focus}\n\nLength: {length_text}\n"
    custom_instruction = (custom_instruction or "").strip()
    if custom_instruction:
        text += (
            "\nExtra requirement from the user (apply it to the rewritten prompt; "
            f"still keep the reply format above): {custom_instruction}\n"
        )
    return text
