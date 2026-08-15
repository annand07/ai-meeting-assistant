"""
AI Video Assistant — Streamlit UI
-----------------------------------
Wraps the existing CLI pipeline (process_input -> transcribe -> summarize ->
extract -> RAG chat) in a polished Streamlit inter"""

import time
import traceback

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# --------------------------------------------------------------------------
# Page config & global styles
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    /* ---- Layout tightening ---- */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* ---- Header ---- */
    .app-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }
    .app-header h1 {
        font-size: 1.9rem;
        margin: 0;
    }
    .app-subtitle {
        color: var(--text-color, #6b7280);
        opacity: 0.75;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
    }

    /* ---- Cards ---- */
    .card {
        background: rgba(127, 127, 127, 0.06);
        border: 1px solid rgba(127, 127, 127, 0.15);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .card h4 {
        margin-top: 0;
        margin-bottom: 0.6rem;
    }

    /* ---- Pills / status badges ---- */
    .pill {
        display: inline-block;
        padding: 0.15rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .pill-done { background: #16a34a22; color: #16a34a; }
    .pill-idle { background: #6b728022; color: #6b7280; }

    /* ---- Chat bubbles spacing ---- */
    .stChatMessage { margin-bottom: 0.4rem; }

    /* ---- Sidebar tweaks ---- */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Session state initialization
# --------------------------------------------------------------------------
defaults = {
    "result": None,            # holds pipeline output dict
    "processing": False,
    "chat_history": [],        # list of {"role": ..., "content": ...}
    "last_source": "",
    "error": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def reset_session():
    st.session_state.result = None
    st.session_state.chat_history = []
    st.session_state.error = None


# --------------------------------------------------------------------------
# Pipeline runner (mirrors run_pipeline from the CLI script, with progress)
# --------------------------------------------------------------------------
def run_pipeline_with_progress(source: str, language: str) -> dict:
    progress = st.progress(0, text="Starting AI Video Assistant…")
    status = st.empty()

    def step(pct, label):
        progress.progress(pct, text=label)
        status.markdown(f"**{label}**")

    step(10, "📥 Fetching & processing input source…")
    chunks = process_input(source)

    step(30, "🎙️ Transcribing audio…")
    transcript = transcribe_all(chunks, language)

    step(50, "🏷️ Generating title…")
    title = generate_title(transcript)

    step(60, "📋 Summarizing content…")
    summary = summarize(transcript)

    step(70, "✅ Extracting action items…")
    action_items = extract_action_items(transcript)

    step(80, "🔑 Extracting key decisions…")
    decisions = extract_key_decisions(transcript)

    step(88, "❓ Extracting open questions…")
    questions = extract_questions(transcript)

    step(95, "🧠 Building RAG chain for chat…")
    rag_chain = build_rag_chain(transcript)

    step(100, "🎉 Done!")
    time.sleep(0.4)
    progress.empty()
    status.empty()

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# --------------------------------------------------------------------------
# Sidebar — input controls
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎬 AI Video Assistant")
    st.caption("Turn any video or audio into a searchable, summarized meeting brief.")
    st.divider()

    input_mode = st.radio(
        "Input type",
        options=["YouTube URL", "Upload local file"],
        horizontal=False,
    )

    source = None
    uploaded_file = None

    if input_mode == "YouTube URL":
        source = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
        )
        st.caption(
            "⚠️ Note: YouTube URL downloads may be blocked on cloud hosting "
            "due to IP restrictions. For best results, use file upload."
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload audio/video file",
            type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
        )
        if uploaded_file is not None:
            import os
            import tempfile

            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = tmp_path

    language = st.selectbox("Language", options=["english", "hinglish"], index=0)

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        run_clicked = st.button("🚀 Process", use_container_width=True, type="primary")
    with col_b:
        reset_clicked = st.button("♻️ Reset", use_container_width=True)

    if reset_clicked:
        reset_session()
        st.rerun()

    st.divider()
    status_label = "✅ Ready" if st.session_state.result else "⏳ Idle"
    pill_class = "pill-done" if st.session_state.result else "pill-idle"
    st.markdown(
        f'<span class="pill {pill_class}">{status_label}</span>',
        unsafe_allow_html=True,
    )

    if st.session_state.result:
        st.markdown("#### 📌 Current video")
        st.write(st.session_state.result.get("title", "—"))

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(
    '<div class="app-header"><h1>🎬 AI Video Assistant</h1></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Transcribe, summarize, extract insights, '
    'and chat with any video or meeting recording.</div>',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Trigger processing
# --------------------------------------------------------------------------
if run_clicked:
    if not source:
        st.error("Please provide a YouTube URL or upload a file before processing.")
    else:
        reset_session()
        st.session_state.processing = True
        try:
            with st.spinner("Working on it… this can take a minute for longer videos."):
                st.session_state.result = run_pipeline_with_progress(source, language)
            st.session_state.last_source = source
            st.toast("Processing complete!", icon="🎉")
        except Exception as e:
            st.session_state.error = str(e)
            st.session_state.error_trace = traceback.format_exc()
        finally:
            st.session_state.processing = False

if st.session_state.error:
    st.error(f"Something went wrong: {st.session_state.error}")
    with st.expander("Show error details"):
        st.code(st.session_state.get("error_trace", ""))

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
result = st.session_state.result

if not result:
    st.info(
        "👈 Enter a YouTube URL or upload a file in the sidebar, then click "
        "**Process** to get started.",
        icon="ℹ️",
    )
else:
    st.markdown(f"## 📌 {result['title']}")

    tabs = st.tabs(
        [
            "📋 Summary",
            "✅ Action Items",
            "🔑 Key Decisions",
            "❓ Open Questions",
            "📝 Transcript",
            "💬 Chat",
        ]
    )

    # --- Summary tab ---
    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(result["summary"])
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download summary",
            data=result["summary"],
            file_name="summary.txt",
            use_container_width=False,
        )

    # --- Action items tab ---
    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        items = result["action_items"]
        if isinstance(items, (list, tuple)):
            for i, item in enumerate(items, 1):
                st.checkbox(str(item), key=f"action_{i}")
        else:
            st.markdown(items)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Key decisions tab ---
    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        decisions = result["key_decisions"]
        if isinstance(decisions, (list, tuple)):
            for d in decisions:
                st.markdown(f"- {d}")
        else:
            st.markdown(decisions)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Open questions tab ---
    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        questions = result["open_questions"]
        if isinstance(questions, (list, tuple)):
            for q in questions:
                st.markdown(f"- {q}")
        else:
            st.markdown(questions)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Transcript tab ---
    with tabs[4]:
        with st.expander("Full transcript", expanded=True):
            st.text_area(
                "Transcript",
                value=result["transcript"],
                height=400,
                label_visibility="collapsed",
            )
        st.download_button(
            "⬇️ Download transcript",
            data=result["transcript"],
            file_name="transcript.txt",
        )

    # --- Chat tab (RAG) ---
    with tabs[5]:
        st.caption("Ask anything about this video — grounded in its transcript.")

        chat_container = st.container(height=420)
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        prompt = st.chat_input("Ask a question about the video…")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        try:
                            answer = ask_question(result["rag_chain"], prompt)
                        except Exception as e:
                            answer = f"⚠️ Error answering question: {e}"
                    st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑️ Clear chat"):
                st.session_state.chat_history = []
                st.rerun()