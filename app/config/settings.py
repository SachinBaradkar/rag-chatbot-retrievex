"""
Central configuration — reads from environment variables with sensible defaults.
The same file works locally (.env) and in any deployment platform.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Base paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOAD_DIR   = Path(os.getenv("UPLOAD_DIR",   str(BASE_DIR / "uploads")))
VECTORDB_DIR = Path(os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "vectordb")))
DATA_DIR     = Path(os.getenv("DATA_DIR",     str(BASE_DIR / "data")))

# Create dirs if they don't exist
for _d in (UPLOAD_DIR, VECTORDB_DIR, DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Embedding model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# ── LLM ───────────────────────────────────────────────────────────────────────
# Options: "groq", "huggingface", "openai_compatible"
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3-8b-8192")

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")          # Free tier – no billing
HF_API_TOKEN   = os.getenv("HF_API_TOKEN", "")          # Optional fallback

# ── ChromaDB ──────────────────────────────────────────────────────────────────
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "rag_documents")

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K              = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

# ── App ───────────────────────────────────────────────────────────────────────
APP_TITLE  = os.getenv("APP_TITLE", "RAG Chatbot")
APP_ENV    = os.getenv("APP_ENV", "development")
DEBUG      = APP_ENV == "development"

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".xlsx", ".json", ".md"}
MAX_UPLOAD_SIZE_MB   = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
