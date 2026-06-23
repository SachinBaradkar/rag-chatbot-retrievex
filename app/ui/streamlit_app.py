"""
Retrievex — Streamlit UI
Run with:  streamlit run app/ui/streamlit_app.py
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

import streamlit as st

from app.config.settings import SUPPORTED_EXTENSIONS
from app.ingestion.pipeline import (
    ingest_file, delete_document, clear_knowledge_base, list_uploaded_documents
)
from app.retrieval.retriever import retrieve, format_context
from app.llm.generator import generate_answer, no_context_response
from app.utils.helpers import truncate, setup_logging

setup_logging()

st.set_page_config(
    page_title="Retrievex",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Hide default streamlit header completely */
header[data-testid="stHeader"] {
    height: 0rem !important;
    display: none !important;
}
/* Remove all top/bottom padding */
.block-container {
    padding-top: 0.3rem !important;
    padding-bottom: 0.2rem !important;
}
/* Remove top margin from first element */
.stMainBlockContainer > div:first-child {
    margin-top: 0 !important;
}
.stChatMessage {
    border-radius: 12px;
    margin-bottom: 0.5rem;
}
.source-card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    line-height: 1.5;
}
.doc-chip {
    background: #181825;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 0.4rem 0.7rem;
    margin-bottom: 0.3rem;
    font-size: 0.82rem;
}
.main-header {
    text-align: center;
    padding: 0.2rem 0 0.1rem 0;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"     not in st.session_state: st.session_state.messages     = []
if "last_sources" not in st.session_state: st.session_state.last_sources = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Retrievex")
    st.markdown("### A RAG Chatbot")
    st.markdown("*Powered by Groq · Llama 3 · ChromaDB*")
    st.divider()

    st.markdown("### Upload Documents")
    ext_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    st.caption(f"Supported: {ext_list}")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        if st.button("Ingest Selected Files", use_container_width=True, type="primary"):
            progress = st.progress(0)
            for i, uf in enumerate(uploaded_files):
                with st.spinner(f"Processing {uf.name}…"):
                    result = ingest_file(uf, uf.name)
                    if result.duplicate:
                        st.info(f"{uf.name} already indexed ({result.chunks_added} chunks)")
                    elif result.success:
                        st.success(f"{uf.name} — {result.chunks_added} chunks, {result.pages_found} pages")
                    else:
                        st.error(f"{uf.name}: {result.error}")
                progress.progress((i + 1) / len(uploaded_files))
            progress.empty()
            st.rerun()

    st.divider()

    st.markdown("### Knowledge Base")
    docs = list_uploaded_documents()

    if not docs:
        st.caption("No documents ingested yet.")
    else:
        st.caption(f"{len(docs)} document(s) · {sum(d['chunks'] for d in docs)} total chunks")
        for doc in docs:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"<div class='doc-chip'>📄 <b>{doc['filename']}</b><br>"
                    f"<span style='color:#888'>{doc['chunks']} chunks · {doc['pages']} pages · {doc['size']}</span></div>",
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("🗑️", key=f"del_{doc['filename']}", help=f"Delete {doc['filename']}"):
                    delete_document(doc["filename"])
                    st.rerun()

        st.markdown("")
        if st.button("Clear Knowledge Base", use_container_width=True):
            clear_knowledge_base()
            st.session_state.messages = []
            st.session_state.last_sources = []
            st.rerun()

    st.divider()
    st.markdown("### Settings")
    top_k      = st.slider("Results to retrieve (K)", min_value=1, max_value=10, value=5)
    use_rerank = st.checkbox("Enable reranking", value=True)
    show_chunks = st.checkbox("Show retrieved chunks", value=True)

    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()

    st.caption("© 2024 Retrievex · Portfolio Project")


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='main-header'><h2>Retrievex</h2>"
    "<p style='margin:0;color:#888;font-size:0.9rem;'>Answers from your documents, instantly</p></div>",
    unsafe_allow_html=True,
)

col_chat, col_sources = st.columns([5, 1.5])

with col_chat:
    # Height tuned so chat input is always visible without scrolling
    chat_container = st.container(height=390)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                """
                <div style="text-align:center; padding:1.5rem; color:#888;">
                <h4>Welcome to Retrievex</h4>
                <p>Upload documents in the sidebar, then ask questions here.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a question about your documents…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        docs_available = bool(list_uploaded_documents())
        if not docs_available:
            answer  = "Please upload at least one document before asking questions."
            sources = []
        else:
            with st.spinner("Searching and generating answer…"):
                hits = retrieve(prompt, k=top_k, rerank=use_rerank)
                if not hits:
                    answer  = no_context_response()
                    sources = []
                else:
                    context = format_context(hits)
                    history = [
                        m for m in st.session_state.messages[:-1]
                        if m["role"] in ("user", "assistant")
                    ]
                    answer  = generate_answer(prompt, context, history)
                    sources = hits

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_sources = sources
        st.rerun()

# ── Sources panel ─────────────────────────────────────────────────────────────
with col_sources:
    st.markdown("### Sources")

    if not st.session_state.last_sources:
        st.caption("Citations appear here after you ask a question.")
    else:
        sources = st.session_state.last_sources
        st.caption(f"{len(sources)} chunk(s) retrieved")

        seen_files: set = set()
        st.markdown("**Referenced Documents:**")
        for h in sources:
            fname = h["metadata"].get("source", "?")
            page  = h["metadata"].get("page",   "?")
            if fname not in seen_files:
                seen_files.add(fname)
                st.markdown(
                    f"<div class='doc-chip'>📄 <b>{fname}</b> · Page {page}</div>",
                    unsafe_allow_html=True,
                )

        if show_chunks:
            st.markdown("**Retrieved Evidence:**")
            for i, h in enumerate(sources, 1):
                meta       = h["metadata"]
                chunk_text = truncate(h["text"], 250)
                st.markdown(
                    f"<div class='source-card'>"
                    f"<b>Chunk {i}</b><br>"
                    f"<small>📄 {meta.get('source','?')} · Page {meta.get('page','?')}</small>"
                    f"<br><br>{chunk_text}"
                    f"</div>",
                    unsafe_allow_html=True,
                )