"""Streamlit demo (issue #18): the same message through the UNPROTECTED and the
PROTECTED pipeline, side by side.   Run:  streamlit run ui/app.py   (from the repo root)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `app` importable

import streamlit as st

from app import injection_ml, pipeline
from app.llm_client import LLMError
from ui.helpers import EXAMPLES, find_leaks, status_of, timing_summary

st.set_page_config(page_title="VN-LLM-Shield", page_icon="🛡️", layout="wide")


@st.cache_resource
def load_classifier() -> bool:
    injection_ml.get_model()  # train the classifier once (under 1 s)
    return True


load_classifier()

st.session_state.setdefault("message", "")
st.session_state.setdefault("role", "employee")


def load_example() -> None:
    ex = EXAMPLES.get(st.session_state["example"])
    if ex:
        st.session_state["message"] = ex["message"]
        st.session_state["role"] = ex["role"]


def run_one(message: str, role: str, switches: pipeline.Switches):
    """Returns (result, error_text). Errors are shown, never crash the page."""
    try:
        return pipeline.chat(message, role, None, switches), None
    except LLMError as e:
        return None, f"LLM error: {e}"
    except Exception as e:  # e.g. missing log encryption key  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def render_panel(title: str, outcome) -> None:
    result, error = outcome
    st.subheader(title)
    if error:
        st.error(error)
        return
    level, text = status_of(result)
    {"blocked": st.error, "warn": st.warning, "ok": st.success}[level](text)

    st.markdown("**Answer**")
    st.write(result.answer)
    if find_leaks(result.answer):
        st.error("⚠️ The answer leaks the internal system code.")

    with st.expander("What the pipeline did", expanded=True):
        st.markdown("**Text sent to the LLM**")
        st.code(result.masked_question, language=None)

        v = result.verdict
        reasons = "; ".join(v.reasons) if v and v.reasons else "none"
        st.markdown(
            f"**Injection verdict:** {v.action} (score {v.score}). Reasons: {reasons}"
        )

        if result.blocked_by == "injection":
            docs = "not reached (blocked before retrieval)"
        else:
            docs = ", ".join(result.retrieved_doc_ids) or "none"
        st.markdown(f"**Retrieved documents:** {docs}")
        if result.quarantined_doc_ids:
            st.markdown(
                f"**Quarantined (injected command found):** "
                f"{', '.join(result.quarantined_doc_ids)}"
            )

        st.caption(timing_summary(result.timings_ms))
        st.table(
            [{"stage": k, "ms": round(ms, 3)} for k, ms in result.timings_ms.items()]
        )


# ---------------- sidebar: protection layers for the right panel ----------------
with st.sidebar:
    st.header("Protection layers")
    st.caption(
        "Apply to the right panel. The left panel always runs with everything off."
    )
    flags = {
        "injection": st.checkbox("Injection detection", True),
        "injection_ml": st.checkbox("ML classifier (off = rules only)", True),
        "pii": st.checkbox("PII masking", True),
        "rag_acl": st.checkbox("RAG access control", True),
        "scan_docs": st.checkbox("Scan retrieved documents", True),
        "output_scan": st.checkbox("Output scan", True),
        "log": st.checkbox("Encrypted log", True),
        "block_on_warn": st.checkbox("Block on warn", False),
    }
    run_unprotected = st.checkbox("Also run the unprotected pipeline", True)
    st.divider()
    st.caption(
        "Known limits: person names are not masked yet; the detectors do not catch "
        "every attack; each request is independent (no chat history)."
    )

# ---------------- main ----------------
st.title("🛡️ VN-LLM-Shield")
st.caption(
    "A security gateway for an enterprise chatbot: the same question, with and "
    "without protection. Local LLM (Ollama), so every call takes several seconds."
)

st.selectbox(
    "Example prompts",
    ["(custom)"] + list(EXAMPLES),
    key="example",
    on_change=load_example,
)
st.text_area("Message", key="message", height=100)
st.selectbox("Role of the user", ["employee", "manager", "admin"], key="role")

if st.button("Send", type="primary", key="send"):
    msg = st.session_state["message"].strip()
    if not msg:
        st.warning("Type a message first.")
    else:
        role = st.session_state["role"]
        results: dict = {"message": msg, "role": role}
        if run_unprotected:
            with st.spinner(
                "Running the unprotected pipeline (LLM on CPU, may take 10-30 s)..."
            ):
                results["off"] = run_one(msg, role, pipeline.Switches.all_off())
        with st.spinner("Running the protected pipeline..."):
            results["on"] = run_one(msg, role, pipeline.Switches(**flags))
        st.session_state["results"] = results

shown = st.session_state.get("results")
if shown:
    st.divider()
    st.markdown(f"**Message:** {shown['message']}  \n**Role:** {shown['role']}")
    if "off" in shown:
        left, right = st.columns(2)
        with left:
            render_panel("❌ Unprotected", shown["off"])
        with right:
            render_panel("✅ Protected", shown["on"])
    else:
        render_panel("✅ Protected", shown["on"])
