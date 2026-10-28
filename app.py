"""Streamlit UI for the AI Prompt Optimizer. Run with: streamlit run app.py"""

import streamlit as st

from optimizer import OptimizerError, optimize_prompt
from prompts import MODES
from storage import load_history, save_entry

st.set_page_config(page_title="AI Prompt Optimizer", page_icon="✨", layout="wide")

# session_state keeps values between Streamlit reruns.
if "result" not in st.session_state:
    st.session_state.result = None  # dict with original/optimized/explanation/mode
if "rough_prompt" not in st.session_state:
    st.session_state.rough_prompt = ""
if "mode" not in st.session_state:
    st.session_state.mode = MODES[0]


def load_from_history(entry: dict) -> None:
    """Callback: put a saved history entry back into the inputs and results."""
    st.session_state.rough_prompt = entry["original"]
    st.session_state.mode = entry["mode"] if entry["mode"] in MODES else MODES[0]
    st.session_state.result = {
        "original": entry["original"],
        "optimized": entry["optimized"],
        "explanation": entry["explanation"],
        "mode": entry["mode"],
    }


# ---------- Sidebar: history ----------
with st.sidebar:
    st.header("🕘 History (last 20)")
    history = load_history(20)
    if not history:
        st.caption("No history yet.")
    for entry in history:
        preview = entry["original"].replace("\n", " ")[:40]
        st.button(
            f"[{entry['mode']}] {preview}",
            key=f"hist_{entry['id']}",
            help=entry["created_at"],
            on_click=load_from_history,
            args=(entry,),
            use_container_width=True,
        )

# ---------- Main: input ----------
st.title("✨ AI Prompt Optimizer")
st.caption("Turn a rough prompt into a clear, specific, structured one.")

st.selectbox("Mode", MODES, key="mode")
st.text_area("Your rough prompt", key="rough_prompt", height=150,
             placeholder="e.g. write code for a todo app")

if st.button("Optimize", type="primary"):
    rough = st.session_state.rough_prompt.strip()
    if not rough:
        st.warning("Please enter a prompt first.")
    else:
        try:
            with st.spinner("Optimizing..."):
                optimized, explanation = optimize_prompt(rough, st.session_state.mode)
            save_entry(st.session_state.mode, rough, optimized, explanation)
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
    left, right = st.columns(2)
    with left:
        st.subheader("Original")
        st.text(result["original"])
    with right:
        st.subheader("Optimized")
        st.write(result["optimized"])
    st.caption("Copy-friendly version (use the copy icon at the top-right of the box):")
    st.code(result["optimized"], language="markdown")
    st.subheader("What improved and why")
    st.markdown(result["explanation"])
