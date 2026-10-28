"""Streamlit UI for the AI Prompt Optimizer. Run with: streamlit run app.py"""

import streamlit as st

import config
import storage
from optimizer import OptimizerError, count_words, optimize_prompt
from prompts import DEFAULT_LENGTH, LENGTHS, MODE_DESCRIPTIONS, MODES

st.set_page_config(page_title="AI Prompt Optimizer", page_icon="✨", layout="wide")

# Minimal custom CSS: hide Streamlit's footer and style the header/tagline.
st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    .app-title {font-size: 2.2rem; font-weight: 700; margin-bottom: 0;}
    .app-tagline {color: #6B7280; margin-top: 0; margin-bottom: 1.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# session_state keeps values between Streamlit reruns.
DEFAULTS = {
    "result": None,            # dict: original / optimized / explanation / mode
    "rough_prompt": "",
    "mode": MODES[0],
    "length": DEFAULT_LENGTH,
    "custom_instruction": "",
    "auto_run": False,         # True after "Optimize again" -> run immediately
    "confirm_clear": False,    # True while waiting for "Clear all" confirmation
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


# ---------- Callbacks (run before the page redraws) ----------

def load_from_history(entry: dict) -> None:
    """Put a saved history entry back into the inputs and results."""
    st.session_state.rough_prompt = entry["original"]
    st.session_state.mode = entry["mode"] if entry["mode"] in MODES else MODES[0]
    st.session_state.result = {
        "original": entry["original"],
        "optimized": entry["optimized"],
        "explanation": entry["explanation"],
        "mode": entry["mode"],
    }


def delete_from_history(entry_id: int) -> None:
    """Delete one history entry."""
    storage.delete_entry(entry_id)


def ask_clear_all() -> None:
    """Show the confirmation question for 'Clear all'."""
    st.session_state.confirm_clear = True


def confirm_clear_all() -> None:
    """Really delete all history."""
    storage.clear_history()
    st.session_state.confirm_clear = False


def cancel_clear_all() -> None:
    """Hide the confirmation question without deleting."""
    st.session_state.confirm_clear = False


def optimize_again() -> None:
    """Use the optimized prompt as the new input and run again on the next redraw."""
    st.session_state.rough_prompt = st.session_state.result["optimized"]
    st.session_state.auto_run = True


# ---------- Sidebar: history ----------
with st.sidebar:
    st.header(f"🕘 History (last {config.HISTORY_LIMIT})")
    history = storage.load_history(config.HISTORY_LIMIT)
    if not history:
        st.caption("No history yet.")
    for entry in history:
        preview = entry["original"].replace("\n", " ")[:30]
        load_col, del_col = st.columns([5, 1])
        load_col.button(f"[{entry['mode']}] {preview}", key=f"hist_{entry['id']}",
                        help=entry["created_at"], on_click=load_from_history,
                        args=(entry,), use_container_width=True)
        del_col.button("🗑", key=f"del_{entry['id']}", help="Delete this entry",
                       on_click=delete_from_history, args=(entry["id"],))

    if history:
        st.divider()
        if st.session_state.confirm_clear:
            st.warning("Delete ALL history? This cannot be undone.")
            yes_col, no_col = st.columns(2)
            yes_col.button("Yes, delete", on_click=confirm_clear_all, type="primary")
            no_col.button("Cancel", on_click=cancel_clear_all)
        else:
            st.button("Clear all history", on_click=ask_clear_all)
        st.download_button("⬇ Export CSV", storage.export_csv(), "prompt_history.csv", "text/csv")
        st.download_button("⬇ Export JSON", storage.export_json(), "prompt_history.json",
                           "application/json")

# ---------- Main: header and input ----------
st.markdown('<p class="app-title">✨ AI Prompt Optimizer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-tagline">Turn a rough idea into a clear, specific, structured prompt.</p>',
            unsafe_allow_html=True)

mode_col, length_col = st.columns(2)
mode_col.selectbox("Mode", MODES, key="mode")
mode_col.caption(MODE_DESCRIPTIONS[st.session_state.mode])
length_col.selectbox("Output length", LENGTHS, key="length")
length_col.caption("How long the optimized prompt should be.")

st.text_area("Your rough prompt", key="rough_prompt", height=150,
             placeholder="e.g. write code for a todo app")
st.caption(f"{len(st.session_state.rough_prompt)} / {config.MAX_INPUT_CHARS} characters")
st.text_input("Custom instruction (optional)", key="custom_instruction",
              placeholder='e.g. "Hinglish mein output" or "keep it short"')

# Run when the button is clicked, or right after "Optimize again".
clicked = st.button("Optimize", type="primary")
auto_run = st.session_state.pop("auto_run", False)
if clicked or auto_run:
    rough = st.session_state.rough_prompt.strip()
    try:
        with st.spinner("Optimizing..."):
            optimized, explanation = optimize_prompt(
                rough, st.session_state.mode, st.session_state.length,
                st.session_state.custom_instruction)
        storage.save_entry(st.session_state.mode, rough, optimized, explanation)
        st.session_state.result = {
            "original": rough,
            "optimized": optimized,
            "explanation": explanation,
            "mode": st.session_state.mode,
        }
        st.rerun()  # refresh so the sidebar history shows the new entry
    except OptimizerError as e:
        st.error(str(e))

# ---------- Main: output ----------
result = st.session_state.result
if result:
    st.divider()
    original_words = count_words(result["original"])
    optimized_words = count_words(result["optimized"])
    m1, m2 = st.columns(2)
    m1.metric("Original words", original_words)
    m2.metric("Optimized words", optimized_words, delta=optimized_words - original_words)

    left, right = st.columns(2)
    with left:
        st.subheader("Original")
        st.text(result["original"])
    with right:
        st.subheader("Optimized")
        st.write(result["optimized"])

    st.caption("Copy-friendly version: click the copy icon at the top-right of the box.")
    st.code(result["optimized"], language="markdown")
    st.button("🔁 Optimize again", on_click=optimize_again,
              help="Use this optimized prompt as the input and improve it once more.")

    st.subheader("What improved and why")
    st.markdown(result["explanation"])
