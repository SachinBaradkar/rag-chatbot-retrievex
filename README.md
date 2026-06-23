---
title: Retrievex
emoji: ⚡
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Retrievex — Intelligent Document Q&A System

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?style=flat-square&logo=streamlit)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-green?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Deployment](https://img.shields.io/badge/Deployed-HuggingFace_Spaces-blue?style=flat-square)

> **Retrievex** is a production-grade Retrieval-Augmented Generation (RAG) application that answers questions strictly based on user-uploaded documents — with source citations, page numbers, and multi-turn conversational memory. Built entirely with free and open-source technologies.

---

## Live Demo

**Deployed on Hugging Face Spaces:**
[https://huggingface.co/spaces/SachinBaradkar/rag-chatbot-retrievex](https://huggingface.co/spaces/SachinBaradkar/rag-chatbot-retrievex)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [RAG Pipeline](#rag-pipeline)
- [Folder Structure](#folder-structure)
- [Local Setup](#local-setup)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Design Decisions](#design-decisions)
- [Limitations & Future Scope](#limitations--future-scope)
- [Cost Breakdown](#cost-breakdown)

---

## Project Overview

Retrievex is a **document-grounded conversational AI system** built on the RAG (Retrieval-Augmented Generation) architecture. Unlike general-purpose chatbots that answer from training data, Retrievex answers **only from documents you upload** — eliminating hallucinations and ensuring every answer is traceable to a source.

### Problem It Solves

Organizations and individuals often need to query large document collections — policy manuals, research papers, legal contracts, technical documentation — without reading every page. Retrievex enables natural language Q&A over any document collection with verifiable, cited answers.

### Core Workflow

```
User uploads document
        ↓
Document is parsed, chunked, and embedded
        ↓
Embeddings stored in ChromaDB vector store
        ↓
User asks a question
        ↓
Question is embedded and matched against stored chunks
        ↓
Top relevant chunks retrieved and reranked
        ↓
Llama 3 generates a grounded answer with citations
        ↓
Answer displayed with source document, page number, and evidence chunks
```

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-format Upload** | Supports PDF, DOCX, TXT, MD, CSV, XLSX, JSON |
| **Intelligent Chunking** | RecursiveCharacterTextSplitter with optimized size and overlap |
| **Local Embeddings** | sentence-transformers running on CPU — zero API cost |
| **Vector Search** | ChromaDB with cosine similarity for semantic retrieval |
| **Cross-encoder Reranking** | ms-marco-MiniLM reranker improves retrieval precision |
| **Free LLM Inference** | Groq API with Llama 3 — no billing, no credit card |
| **Source Citations** | Every answer cites document name and page number |
| **Evidence Chunks** | Retrieved text chunks displayed alongside answers |
| **Conversational Memory** | Multi-turn conversation with context retention |
| **Duplicate Detection** | SHA-256 hashing prevents re-ingesting same file |
| **Document Management** | Delete individual documents or clear entire knowledge base |
| **Single Codebase** | Same code runs locally and on HuggingFace Spaces |
| **Dark Mode UI** | Professional Catppuccin-themed Streamlit interface |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Retrievex                                 │
│                     Streamlit Frontend                           │
│         Sidebar          │    Chat Area    │   Sources Panel     │
└──────────┬───────────────────────────────────────┬──────────────┘
           │ Upload                                │ Query
           ▼                                       ▼
┌─────────────────────┐              ┌─────────────────────────┐
│  Ingestion Pipeline │              │    Retrieval Engine      │
│                     │              │                          │
│  File Loaders       │              │  Similarity Search       │
│  (7 formats)        │              │  (ChromaDB cosine)       │
│         ↓           │              │         ↓                │
│  Text Chunker       │              │  Cross-Encoder Rerank    │
│  (Recursive)        │              │  (ms-marco-MiniLM)       │
│         ↓           │              │         ↓                │
│  Duplicate Check    │              │  Context Assembly        │
│  (SHA-256)          │              │  + Chat History          │
└──────────┬──────────┘              └─────────────┬───────────┘
           │                                       │
           ▼                                       ▼
┌─────────────────────┐              ┌─────────────────────────┐
│  Embedding Model    │              │     Groq LLM API         │
│  all-MiniLM-L6-v2   │              │     Llama 3 8B           │
│  (Local — CPU)      │              │     (Free Tier)          │
└──────────┬──────────┘              └─────────────────────────┘
           │
           ▼
┌─────────────────────┐
│     ChromaDB        │
│  (Persistent Local  │
│   Vector Store)     │
└─────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose | Cost |
|---|---|---|---|
| **Frontend** | Streamlit 1.35+ | Web UI | Free |
| **LLM** | Groq + Llama 3 8B | Answer generation | Free tier |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Text vectorization | Free (local) |
| **Vector DB** | ChromaDB 0.5+ | Semantic search | Free (local) |
| **Reranker** | cross-encoder/ms-marco-MiniLM-L-6-v2 | Result reranking | Free (local) |
| **PDF Parsing** | pdfplumber | Page-level PDF extraction | Free |
| **DOCX Parsing** | python-docx | Word document parsing | Free |
| **XLSX Parsing** | openpyxl | Excel spreadsheet parsing | Free |
| **Text Splitting** | LangChain RecursiveCharacterTextSplitter | Intelligent chunking | Free |
| **Deployment** | Hugging Face Spaces (Docker) | Cloud hosting | Free |
| **Containerization** | Docker | Deployment packaging | Free |

---

## RAG Pipeline

### 1. Document Loading
Each file format has a dedicated loader:
- **PDF** — pdfplumber with page-level metadata extraction
- **DOCX** — python-docx paragraph extraction
- **CSV** — row-grouped batches with header-value formatting
- **XLSX** — sheet-aware extraction with column headers
- **JSON** — structured dump with indentation
- **TXT/MD** — direct UTF-8 read

### 2. Chunking Strategy
```
RecursiveCharacterTextSplitter
  chunk_size    = 800 characters
  chunk_overlap = 150 characters
  separators    = ["\n\n", "\n", ". ", " ", ""]
```
Overlap ensures context continuity across chunk boundaries. Separators prioritize semantic breaks (paragraphs → sentences → words).

### 3. Embedding
`sentence-transformers/all-MiniLM-L6-v2` — a 22M parameter model producing 384-dimensional vectors. Chosen for:
- Runs entirely on CPU — no GPU required
- Strong semantic similarity performance
- ~80MB model size — fast to download and load
- No API calls — zero cost, works offline

### 4. Vector Storage
ChromaDB with `hnsw:space=cosine` for cosine similarity. Chunks are stored with metadata: source filename, page number, chunk index, file type.

### 5. Retrieval
- Query is embedded with the same model
- Top-K nearest chunks retrieved by cosine similarity
- Cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) rescores and reorders results
- Reranking significantly improves precision — especially for ambiguous queries

### 6. Answer Generation
Retrieved chunks are assembled into a structured context prompt. Groq's Llama 3 8B generates answers under a strict system prompt:
- Answer only from provided context
- Cite sources naturally in the answer
- Explicitly state when information is not found
- Maintain conversational context from last 3 exchanges

---

## Folder Structure

```
retrievex/
├── app/
│   ├── config/
│   │   └── settings.py          # Environment-based configuration
│   ├── embeddings/
│   │   └── embedder.py          # Local sentence-transformer embeddings
│   ├── ingestion/
│   │   ├── loaders.py           # File-type loaders (7 formats)
│   │   ├── chunker.py           # RecursiveCharacterTextSplitter
│   │   └── pipeline.py          # Full ingestion orchestration
│   ├── retrieval/
│   │   └── retriever.py         # Similarity search + reranking
│   ├── llm/
│   │   └── generator.py         # Groq LLM answer generation
│   ├── vectorstore/
│   │   └── chroma_store.py      # ChromaDB vector store wrapper
│   ├── ui/
│   │   └── streamlit_app.py     # Complete Streamlit UI
│   └── utils/
│       └── helpers.py           # Shared utility functions
├── uploads/                     # Uploaded documents (runtime)
├── data/                        # Manifest and metadata (runtime)
├── vectordb/                    # ChromaDB persistence (runtime)
├── sample_docs/                 # Sample documents for testing
├── tests/
│   └── test_core.py             # Pytest unit tests
├── .streamlit/
│   └── config.toml              # Streamlit theme and server config
├── Dockerfile                   # Docker deployment config
├── app.py                       # HuggingFace Spaces entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
├── run.py                       # Local launcher
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- Git
- Free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/SachinBaradkar/rag-chatbot-retrievex.git
cd rag-chatbot-retrievex

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Environment Variables

```env
GROQ_API_KEY=gsk_your_key_here
LLM_PROVIDER=groq
LLM_MODEL_NAME=llama-3.1-8b-instant
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K=5
SIMILARITY_THRESHOLD=0.1
MAX_UPLOAD_SIZE_MB=50
```

### Run

```bash
python run.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Deployment

Deployed using Docker on Hugging Face Spaces (free tier).

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads data vectordb
EXPOSE 7860
CMD ["streamlit", "run", "app/ui/streamlit_app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

**Why Hugging Face Spaces?**
- Free permanent hosting with 2 vCPU + 16GB RAM
- Native Docker support
- Environment secrets management
- No credit card required

---

## Usage Guide

### 1. Upload Documents
- Click **Upload Documents** in the sidebar
- Select one or multiple files (PDF, DOCX, TXT, MD, CSV, XLSX, JSON)
- Click **Ingest Selected Files**
- Wait for confirmation — chunks and pages count displayed

### 2. Ask Questions
- Type your question in the chat input
- Retrievex searches the knowledge base and generates a grounded answer
- Sources panel shows referenced documents, page numbers, and evidence chunks

### 3. Follow-up Questions
- Ask follow-up questions naturally — conversation context is maintained
- Example:
  - *"What is the leave policy?"*
  - *"How does that compare to sick leave?"* ← uses context

### 4. Manage Documents
- Delete individual documents using the 🗑️ button
- Clear entire knowledge base with **Clear Knowledge Base**

### Sample Queries

After uploading a company policy document:
```
What is the annual leave entitlement?
What is the notice period for resignation?
Explain the grievance procedure step by step.
What are the remote work guidelines?
```

After uploading a research paper:
```
What problem does this paper solve?
What methodology was used?
What were the key findings?
Who are the authors?
```

---

## Design Decisions

### Why Groq over OpenAI?
Groq provides a completely free tier with no credit card requirement, running Llama 3 on custom LPU hardware with sub-second latency. OpenAI charges per token — unsuitable for a free, portfolio-grade project.

### Why ChromaDB over Pinecone?
ChromaDB runs locally with zero configuration and persists to disk. Pinecone requires account creation and has usage limits on the free tier. For a single-user deployment, local ChromaDB is simpler and faster.

### Why sentence-transformers over OpenAI embeddings?
OpenAI embeddings cost money per token. sentence-transformers runs entirely on CPU, requires no API key, and delivers strong semantic similarity performance for document retrieval tasks.

### Why RecursiveCharacterTextSplitter?
It respects semantic boundaries (paragraphs before sentences before words) and is battle-tested across thousands of RAG implementations. Semantic chunking was considered but requires an LLM call per chunk — too slow and costly for a free-tier application.

### Why cross-encoder reranking?
Bi-encoder retrieval (embedding similarity) is fast but imprecise. Cross-encoders compare query and document together, significantly improving precision on ambiguous queries at the cost of slightly higher latency — an acceptable tradeoff for answer quality.

---

## Limitations & Future Scope

### Current Limitations

| Limitation | Reason |
|---|---|
| No user authentication | Phase 1 scope — single user demo |
| Shared knowledge base | All users see same documents |
| No persistent chat history | Streamlit session state only |
| HF Space sleeps after 48h inactivity | Free tier constraint |
| Scanned PDFs not supported | Requires OCR (pytesseract) |

### Phase 2 — Planned Improvements

- **User Authentication** — Supabase Auth with Google/GitHub OAuth
- **Per-user Document Isolation** — Qdrant Cloud with user-scoped collections
- **Cloud Document Storage** — Supabase Storage (1GB free)
- **Persistent Chat History** — Supabase PostgreSQL
- **OCR Support** — pytesseract for scanned PDFs
- **Streaming Responses** — Token-by-token LLM output
- **Document Summarization** — Auto-summarize on upload

---

## Cost Breakdown

| Component | Service | Cost |
|---|---|---|
| LLM Inference | Groq free tier | $0 |
| Embeddings | Local sentence-transformers | $0 |
| Vector Database | ChromaDB local | $0 |
| Hosting | Hugging Face Spaces | $0 |
| Document Storage | Local filesystem | $0 |
| **Total** | | **$0/month** |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Expected output:
```
tests/test_core.py::test_settings_import PASSED
tests/test_core.py::test_chunker PASSED
tests/test_core.py::test_text_loader PASSED
tests/test_core.py::test_helpers PASSED
tests/test_core.py::test_embeddings PASSED
5 passed
```

---

## License

MIT License — free to use, modify, and deploy.

---

## Author

**Sachin Baradkar**
- GitHub: [github.com/SachinBaradkar](https://github.com/SachinBaradkar)
- Project: [Retrievex on HuggingFace](https://huggingface.co/spaces/SachinBaradkar/rag-chatbot-retrievex)

---

*Built as a portfolio project demonstrating production-grade RAG architecture using entirely free and open-source technologies.*