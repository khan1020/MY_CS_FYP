# chat bot 3 api.py (fixed & consolidated)
# Profile / account management + embed/FAISS + JWT auth
import os
import time
import logging
import threading
import pickle   
from typing import List, Tuple, Dict
from functools import wraps

import io
import zipfile
import json
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from werkzeug.utils import secure_filename, safe_join
from werkzeug.security import generate_password_hash, check_password_hash

# ML libs (optional runtime heavy)
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from openai import OpenAI

# Other
from flask_cors import CORS
import jwt
import MySQLdb

# local auth helpers you already had (ensure functions exist)
from auth import create_user, authenticate_user, generate_token, generate_otp, send_otp_email, verify_otp
import config

from vision_handler import VisionHandler
# Enhanced RAG modules
from query_classifier import classify_query, QueryClassifier
from keyword_extractor import extract_keywords, count_word_frequency, get_document_stats
from hybrid_retriever import hybrid_search, HybridRetriever
from free_tools import search_wikipedia, get_weather, calculate
from query_history import save_query_to_history, QueryHistoryManager
from bookmark_manager import BookmarkManager, create_bookmark, get_bookmarks, export_bookmarks_to_pdf
from template_manager import TemplateManager, get_templates, execute_template

from enhanced_extraction import (
    extract_paragraphs_from_pdf_enhanced,
    extract_text_from_txt_enhanced,
    extract_text_from_docx_enhanced,
    extract_text_from_file_enhanced,
    chunks_to_paragraphs
)

# Try to import BM25 (optional)
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("BM25 not available - hybrid retrieval will use semantic only")




# ----------------- Configuration -----------------
PDF_PATH = os.environ.get("PDF_PATH", "")
MODEL_PATH = os.environ.get("SENTENCE_TRANSFORMER_PATH", "sentence-transformers/all-MiniLM-L6-v2")
FAISS_INDEX_PATH = os.environ.get("FAISS_INDEX_PATH", "faiss_index.bin")
PARAGRAPHS_PATH = os.environ.get("PARAGRAPHS_PATH", "paragraphs.pkl")
INDEX_META_PATH = FAISS_INDEX_PATH + ".meta.pkl"
# OPENROUTER API Configuration - loaded from environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "openai/gpt-4o-mini")

if not OPENROUTER_API_KEY:
    logging.warning("OPENROUTER_API_KEY not set in environment - LLM features will be disabled")

MAX_CONTEXT_CHARS = int(os.environ.get("MAX_CONTEXT_CHARS", "5000"))
TOP_K = int(os.environ.get("TOP_K", "40"))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "passwd": os.environ.get("DB_PASSWORD", ""),
    "db": os.environ.get("DB_NAME", "chatbotdb"),
    "charset": "utf8mb4"
}

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"

ALLOWED_EXTENSIONS = {
    'pdf', 'txt', 'doc', 'docx', 'json',
    'csv', 'jpg', 'jpeg', 'png', 'gif',
    'xlsx', 'pptx', 'rtf', 'md', 'html', 'xml'
}
# Legacy upload folder (deprecated, kept for backward compatibility)
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
MAX_FILE_SIZE = 23 * 1024 * 1024  # 23MB

# New centralized user data folder structure
USER_DATA_FOLDER = os.environ.get("USER_DATA_FOLDER", "user_data")
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif'}
MAX_PROFILE_PIC_BYTES = 2 * 1024 * 1024  # 2 MB

# Helper functions for user data paths
def get_user_data_path(user_id: int, subfolder: str = "") -> str:
    """Get the path to a user's data folder or subfolder.
    
    Structure:
    user_data/
    └── user_<id>/
        ├── profile/       # Profile picture
        ├── uploads/       # PDFs, docs, images
        ├── indexes/       # FAISS index files
        ├── paragraphs/    # Extracted text paragraphs
        ├── recordings/    # Voice recordings
        └── exports/       # Chat exports
    """
    base_path = os.path.join(USER_DATA_FOLDER, f"user_{user_id}")
    if subfolder:
        return os.path.join(base_path, subfolder)
    return base_path

def ensure_user_folders(user_id: int) -> dict:
    """Create all standard folders for a user and return paths dict."""
    paths = {
        "base": get_user_data_path(user_id),
        "profile": get_user_data_path(user_id, "profile"),
        "uploads": get_user_data_path(user_id, "uploads"),
        "indexes": get_user_data_path(user_id, "indexes"),
        "paragraphs": get_user_data_path(user_id, "paragraphs"),
        "recordings": get_user_data_path(user_id, "recordings"),
        "exports": get_user_data_path(user_id, "exports"),
    }
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    return paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doc-chatbot")

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
#working ngrok tunnel link https://d81916b5db93.ngrok-free.app
# CORS
CORS(app, resources={r"/*": {"origins": ["http://localhost", "https://e13febe3a5e1.ngrok-free.app", "http://127.0.0.1:5000"],
                             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                             "supports_credentials": True}})

# preflight handler (returns early for OPTIONS)
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "http://localhost"))
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

# Legacy folders removed - now using user_data/<user_id>/ structure
# Folders are created per-user via ensure_user_folders()

# ----------------- Globals -----------------
_user_indices = {}  # in-memory FAISS indices per user
_user_bm25_indices = {}  # BM25 indices per user for keyword search

_user_data_lock = threading.Lock()

_sent_transformer = None
_faiss_index = None
_paragraphs = []
_embeddings = None
_index_built_at = 0.0
_indexed_pdf_path = ""



# LLM client
client = None
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
        logger.info("LLM client configured")
    except Exception:
        logger.exception("Failed to create LLM client")
        client = None
else:
    logger.warning("OPENROUTER_API_KEY not provided; LLM calls will be disabled/placeholder")

# ----------------- DB -----------------
def get_db_connection():
    try:
        return MySQLdb.connect(**DB_CONFIG)
    except MySQLdb.Error as e:
        logger.error("Database connection failed: %s", e)
        raise

# ----------------- Auth -----------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            # data must contain user_id
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Invalid token payload'}), 401

            db = get_db_connection()
            cursor = db.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            db.close()
            if not user:
                return jsonify({'error': 'Invalid user'}), 401

            # attach to request context
            request.user_id = user_id
            request.user_email = user.get('email')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.exception("Token validation error: %s", e)
            return jsonify({'error': 'Token validation failed'}), 401

        return f(*args, **kwargs)
    return decorated

# Guest Mode Support: Optional authentication decorator
def token_optional(f):
    """Allow both authenticated and guest users"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        
        if token:
            # Attempt regular authentication
            try:
                data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = data.get('user_id')
                if user_id:
                    db = get_db_connection()
                    cursor = db.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    cursor.close()
                    db.close()
                    if user:
                        request.user_id = user_id
                        request.user_email = user.get('email')
                        request.is_guest = False
                        return f(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Token validation failed, treating as guest: {e}")
        
        # Guest mode
        request.user_id = None
        request.user_email = None
        request.is_guest = True
        return f(*args, **kwargs)
    return decorated


# ----------------- Helpers -----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT

# text extraction helpers (kept as you had)
def extract_paragraphs_from_pdf(path: str) -> List[Dict]:
    """Extract paragraphs from PDF WITH PAGE TRACKING"""
    try:
        doc = fitz.open(path)
    except Exception as e:
        logger.exception("Failed to open PDF: %s", path)
        return []
    
    chunks = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if not text:
            continue
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [line.strip() for line in text.splitlines() if line.strip()]
        
        for para_text in parts:
            if para_text:
                chunks.append({
                    'text': para_text,
                    'page_number': page_num,
                    'word_count': len(para_text.split())
                })
    
    logger.info("Extracted %d chunks from %d pages in PDF %s", len(chunks), doc.page_count, path)
    return chunks

def extract_text_from_txt(path: str) -> List[str]:
    try:
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paras:
            paras = [line.strip() for line in text.splitlines() if line.strip()]
        logger.info("Extracted %d paragraphs from TXT %s", len(paras), path)
        return paras
    except Exception:
        logger.exception("Failed to read TXT file: %s", path)
        return []

def extract_text_from_docx(path: str) -> List[str]:
    try:
        import docx
        doc = docx.Document(path)
        paras = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paras.append(text)
        logger.info("Extracted %d paragraphs from DOCX %s", len(paras), path)
        return paras
    except Exception:
        logger.exception("Failed to read DOCX file: %s", path)
        return []

def extract_text_from_file(path: str) -> List[str]:
    file_extension = path.split('.')[-1].lower()
    if file_extension == 'pdf':
        return extract_paragraphs_from_pdf(path)
    elif file_extension == 'txt':
        return extract_text_from_txt(path)
    elif file_extension in ['doc', 'docx']:
        return extract_text_from_docx(path)
    else:
        logger.warning("Unsupported file type for text extraction: %s", file_extension)
        return []
    
#Image handling with VisionHandler start
#Image handling with VisionHandler start
#Image handling with VisionHandler start

# vh = VisionHandler(blip_model_path=r"C:\xampp\htdocs\backend_latest\model\~\models\blip")
# Initialize with proper error handling
try:
    vh = VisionHandler(blip_model_path=r"C:\xampp\htdocs\backend_latest\model\~\models\blip")
    logger.info("VisionHandler initialized successfully on device: %s", vh._device)
except Exception as e:
    logger.error("Failed to initialize VisionHandler: %s", e)
    vh = None

# Image processing helper functions
def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using VisionHandler OCR"""
    if vh is None:
        logger.warning("VisionHandler not available for OCR")
        return ""
    try:
        return vh.extract_text(image_path)
    except Exception as e:
        logger.exception("OCR extraction failed for image: %s", image_path)
        return ""

def describe_image(image_path: str) -> str:
    """Generate description of image using VisionHandler BLIP"""
    if vh is None:
        logger.warning("VisionHandler not available for image description")
        return "Image (vision features unavailable)"
    try:
        return vh.describe_image(image_path)
    except Exception as e:
        logger.exception("Image description failed: %s", image_path)
        return "Image (description unavailable)"
    
#Image handling with VisionHandler start
#Image handling with VisionHandler start
#Image handling with VisionHandler start


    



def build_index_from_text_for_user(user_id: int, text_content: str, source_name: str = "uploaded_text") -> Tuple[faiss.Index, List[str], np.ndarray]:
    """Create paragraphs from plain text (or description), embed and create a FAISS index
       and store under _user_indices like build_index_for_user does.
    """
    # break into paragraphs (simple heuristic)
    paras = [p.strip() for p in text_content.split("\n\n") if p.strip()]
    if not paras:
        paras = [line.strip() for line in text_content.splitlines() if line.strip()]
    if not paras:
        # fallback to whole text
        paras = [text_content.strip()] if text_content.strip() else []
    if not paras:
        raise RuntimeError("No text content to index")
    embeddings, model = embed_paragraphs(paras, MODEL_PATH)
    index = create_faiss_index(embeddings)
    with _user_data_lock:
        _user_indices.setdefault(user_id, {})
        _user_indices[user_id]["index"] = index
        _user_indices[user_id]["paragraphs"] = paras
        _user_indices[user_id]["embeddings"] = embeddings
        _user_indices[user_id]["index_built_at"] = time.time()
        _user_indices[user_id]["file_path"] = os.path.abspath(source_name)
    return index, paras, embeddings


  


def embed_paragraphs(pars, model_path: str) -> Tuple[np.ndarray, SentenceTransformer]:
    """Embed paragraphs - handles both dict format (with 'text' key) and plain strings"""
    global _sent_transformer
    if _sent_transformer is None:
        logger.info("Loading SentenceTransformer model from %s", model_path)
        _sent_transformer = SentenceTransformer(model_path)
    model = _sent_transformer
    
    # Extract text from dicts if needed
    texts_to_embed = []
    for p in pars:
        if isinstance(p, dict):
            texts_to_embed.append(p.get('text', ''))
        else:
            texts_to_embed.append(str(p))
    
    embs = model.encode(texts_to_embed, batch_size=32, show_progress_bar=True, convert_to_numpy=True)
    embs = np.asarray(embs, dtype="float32")
    faiss.normalize_L2(embs)
    logger.info("Created embeddings with shape %s", embs.shape)
    return embs, model


def create_faiss_index(embs: np.ndarray) -> faiss.Index:
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.ascontiguousarray(embs))
    logger.info("FAISS index created and %d vectors added (dim=%d)", index.ntotal, dim)
    return index

def persist_index_and_paragraphs(index: faiss.Index, paragraphs: List[str],
                                 index_path: str, paragraphs_path: str,
                                 meta_path: str, meta: dict):
    try:
        faiss.write_index(index, index_path)
        with open(paragraphs_path, "wb") as f:
            pickle.dump(paragraphs, f)
        meta_to_write = dict(meta)
        meta_to_write.setdefault("built_at", time.time())
        if "file_path" not in meta_to_write and "pdf_path" in meta_to_write:
            meta_to_write["file_path"] = meta_to_write.pop("pdf_path")
        with open(meta_path, "wb") as f:
            pickle.dump(meta_to_write, f)
        logger.info("Persisted FAISS index -> %s, paragraphs -> %s, meta -> %s", index_path, paragraphs_path, meta_path)
    except Exception:
        logger.exception("Failed to persist index/paragraphs/meta")

def load_index_and_paragraphs(index_path: str, paragraphs_path: str, meta_path: str,
                              expected_file_path: str) -> Tuple[faiss.Index, List[str], dict]:
    try:
        if os.path.exists(index_path) and os.path.exists(paragraphs_path) and os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                meta = pickle.load(f)
            meta_file_path = meta.get("file_path", "") or meta.get("pdf_path", "")
            if expected_file_path:
                if os.path.abspath(meta_file_path) != os.path.abspath(expected_file_path):
                    logger.info("Persisted index built from different file (%s) vs expected (%s).", meta_file_path, expected_file_path)
                    return None, None, None
            idx = faiss.read_index(index_path)
            with open(paragraphs_path, "rb") as f:
                pars = pickle.load(f)
            logger.info("Loaded persisted FAISS index and paragraphs (%d paragraphs) for file %s", len(pars), meta_file_path)
            return idx, pars, meta
    except Exception:
        logger.exception("Failed to load persisted index/paragraphs/meta")
    return None, None, None

def search_relevant_paragraphs_for_user(user_id: int, query: str, top_k: int = TOP_K) -> List[str]:
    if not query:
        return []
    with _user_data_lock:
        user_data = _user_indices.get(user_id)
    if not user_data:
        return []
    index = user_data.get("index")
    paragraphs = user_data.get("paragraphs")
    if not index or not paragraphs:
        return []
    q_vec = _sent_transformer.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_vec)
    q_vec = np.ascontiguousarray(q_vec)
    distances, indices = index.search(q_vec, top_k)
    hits = []
    for idx in indices[0]:
        if idx < 0 or idx >= len(paragraphs):
            continue
        hits.append(paragraphs[idx])
    return hits


def search_by_page(user_id: int, page_number: int, keyword: str = None) -> List[Dict]:
    """Search for content on a specific page"""
    with _user_data_lock:
        user_data = _user_indices.get(user_id)
    
    if not user_data or not user_data.get('paragraphs'):
        return []
    
    paragraphs = user_data.get('paragraphs', [])
    results = []
    
    for para in paragraphs:
        # Handle both old (string) and new (dict) format
        if isinstance(para, dict):
            if para.get('page_number') == page_number:
                if keyword:
                    if keyword.lower() in para.get('text', '').lower():
                        results.append(para)
                else:
                    results.append(para)
        elif isinstance(para, str):
            # Old format - can't filter by page
            continue
    
    return results


def get_page_content(user_id: int, page_number: int) -> str:
    """Get all content from a specific page"""
    results = search_by_page(user_id, page_number)
    if results:
        return "\n\n".join([r.get('text', '') if isinstance(r, dict) else r for r in results])
    return f"No content found for page {page_number}"


def ask_model(context: str, query: str, client: OpenAI, model_name: str, stream: bool = False):
    if client is None:
        return "[LLM client not configured]"

    system_prompt = (
        "You are an intelligent, accurate, and helpful AI assistant. Follow these guidelines:\n"
        "**Accuracy First:** Always provide factually correct answers. Do not hallucinate. When unsure, clearly state uncertainty.\n"
        "2. **Use Context:** Use any provided context to tailor your answer.\n"
        "   - **IMPORTANT**: If the context contains real-time information (weather, Wikipedia data, current events), YOU MUST USE IT and present it as current, factual information.\n"
        "   - When weather data is provided in the context (temperature, humidity, location), state it directly as the current weather.\n"
        "   - When Wikipedia or real-time data is provided, use it to answer the question with current information.\n"
        "   - DO NOT say 'I don't have access to real-time data' if real-time data is provided in the context above.\n"
        "3. **Answer Style:**\n"
        " - For complex or multi-part questions: use structured markdown with headings and bullet points.\n"
        " - For simple questions (definitions, greetings, yes/no, casual chat): answer naturally in plain text.\n"
        "4. **CODE FORMATTING (CRITICAL):**\n"
        " - ALWAYS wrap code in fenced code blocks using triple backticks with the language name\n"
        " - Format: ```python then code with proper indentation and newlines then ``` on new line\n"
        " - NEVER put code in a single line - preserve all newlines and indentation\n"
        " - Always specify language: python, javascript, java, html, css, sql, etc.\n"
        "5. **Humor & Personality:** Add light humor or playful tone occasionally when the conversation is casual or friendly.\n"
        "5. **Opinions:** Offer your best opinion when asked or when it adds value, clearly marking it as \"In my opinion:\"\n"
        "6. **Conciseness & Completeness:** Be clear and complete without unnecessary verbosity.\n"
        "7. **Adaptability:** Match tone and style to the context—professional for serious questions, casual for normal conversation.\n"
        "8. **References:** Provide sources when relevant or asked.\n\n"
        "Optional Example:\n"
        "- Simple greeting → \"Hi! How's it going?\"\n"
        "- Definition → Concise paragraph\n"
        "- Complex explanation → Structured markdown\n"
        "- Opinion → Prefixed with \"In my opinion:\"\n"
        "- Weather query with context → \"The current weather in [location] is [temp]°C, [conditions]. Humidity is [X]%.\"\n"
        "9. Developed by Team of University of Sindh Students batch 2k22 included as Afzal Khan, Ghulam Murtaza and Noor Rasheed Ahmed."
    )
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + " ... (truncated)"
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=512,
            temperature=0.1,
            stream=stream  # Pass the stream flag here
        )
        if not stream:
            # Non-streaming: Return full string
            return response.choices[0].message.content.strip()
        else:
            # Streaming: Return generator yielding chunks
            def stream_generator():
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
            return stream_generator()
    except Exception as e:
        logger.exception("LLM request failed: %s", e)
        return f"[Error contacting model] {e}"


def generate_chat_title(first_message: str, first_response: str) -> str:
    """Generate a 3-4 keyword title for a chat based on the first exchange"""
    if client is None:
        # Fallback: extract keywords manually from the user's message
        words = first_message.split()[:4]
        title = ' '.join(words)
        return (title[:30] + '...') if len(title) > 30 else title
    
    try:
        prompt = f"""Generate a short, descriptive title (3-4 keywords max, under 40 characters) for a chat conversation.
User asked: "{first_message[:150]}"
AI responded about: "{first_response[:200]}"

Return ONLY the title text, no quotes, no explanation, no punctuation at the end.
Examples of good titles: "Python Data Analysis", "Machine Learning Basics", "Recipe for Pasta", "Travel Tips Europe" """

        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=25,
            temperature=0.3
        )
        title = response.choices[0].message.content.strip()
        # Clean up: remove quotes and limit length
        title = title.strip('"\'').strip()[:40]
        return title if title else "New Chat"
    except Exception as e:
        logger.exception("Failed to generate chat title: %s", e)
        # Fallback to simple extraction
        words = first_message.split()[:4]
        title = ' '.join(words)
        return (title[:30] + '...') if len(title) > 30 else (title if title else "New Chat")


# Build index wrapper (for /reindex route)
def build_index_from_file(file_path: str):
    paragraphs = extract_text_from_file(file_path)
    if not paragraphs:
        raise RuntimeError("No text extracted from file")
    embeddings, model = embed_paragraphs(paragraphs, MODEL_PATH)
    index = create_faiss_index(embeddings)
    return index, paragraphs, embeddings

# Build index for a user (keeps in-memory)
def build_index_for_user(user_id: int, file_path: str) -> Tuple[faiss.Index, List[str], np.ndarray]:
    paragraphs = extract_text_from_file(file_path)
    if not paragraphs:
        raise RuntimeError("No text extracted from file")
    embeddings, model = embed_paragraphs(paragraphs, MODEL_PATH)
    index = create_faiss_index(embeddings)
    with _user_data_lock:
        _user_indices.setdefault(user_id, {})
        _user_indices[user_id]["index"] = index
        _user_indices[user_id]["paragraphs"] = paragraphs
        _user_indices[user_id]["embeddings"] = embeddings
        _user_indices[user_id]["index_built_at"] = time.time()
        _user_indices[user_id]["file_path"] = file_path
    return index, paragraphs, embeddings

# ----------------- Initialization -----------------
def initialize():
    global _sent_transformer, _faiss_index, _paragraphs, _embeddings, _index_built_at, _indexed_pdf_path
    try:
        _sent_transformer = SentenceTransformer(MODEL_PATH)
        logger.info("Loaded SentenceTransformer model from %s", MODEL_PATH)
    except Exception:
        logger.exception("Failed to load SentenceTransformer model")
        _sent_transformer = None
    _faiss_index = None
    _paragraphs = []
    _embeddings = None
    _index_built_at = 0.0
    _indexed_pdf_path = ""
    if PDF_PATH and os.path.exists(PDF_PATH):
        idx, pars, meta = load_index_and_paragraphs(FAISS_INDEX_PATH, PARAGRAPHS_PATH, INDEX_META_PATH, PDF_PATH)
        if idx is not None:
            _faiss_index = idx
            _paragraphs = pars
            _index_built_at = meta.get("built_at", time.time())
            _indexed_pdf_path = meta.get("file_path", "")
            logger.info("Using persisted index for %s (built at %s)", _indexed_pdf_path, time.ctime(_index_built_at))
        else:
            try:
                _paragraphs = extract_text_from_file(PDF_PATH)
                if _paragraphs:
                    _embeddings, _sent_transformer = embed_paragraphs(_paragraphs, MODEL_PATH)
                    _faiss_index = create_faiss_index(_embeddings)
                    _index_built_at = time.time()
                    _indexed_pdf_path = os.path.abspath(PDF_PATH)
                    meta = {"file_path": _indexed_pdf_path, "file_type": PDF_PATH.split('.')[-1].lower(), "built_at": _index_built_at}
                    persist_index_and_paragraphs(_faiss_index, _paragraphs, FAISS_INDEX_PATH, PARAGRAPHS_PATH, INDEX_META_PATH, meta)
                    logger.info("Created new index from default file: %s", PDF_PATH)
                else:
                    logger.warning("No paragraphs extracted from default file: %s", PDF_PATH)
            except Exception:
                logger.exception("Failed to create index from default file")

initialize()

# ----------------- Auto-delete worker -----------------
AUTO_DELETE_MAPPING = {
    '1min': timedelta(minutes=1),
    '1day': timedelta(days=1),
    '1week': timedelta(weeks=1),
    '1month': timedelta(days=30),
    '1year': timedelta(days=365),
    'never': None
}

def run_auto_delete_worker(interval_seconds=60):
    def worker():
        logger.info("Auto-delete worker started")
        while True:
            try:
                db = get_db_connection()
                cursor = db.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT id, auto_delete FROM users WHERE auto_delete IS NOT NULL AND auto_delete != 'never'")
                rows = cursor.fetchall()
                for u in rows:
                    user_id = u['id']
                    policy = u.get('auto_delete')
                    delta = AUTO_DELETE_MAPPING.get(policy)
                    if not delta:
                        continue
                    cutoff = datetime.utcnow() - delta
                    # delete messages older than cutoff for that user's chats
                    cursor.execute("""
                        DELETE m FROM messages m
                        JOIN chats c ON m.chat_id = c.id
                        WHERE c.user_id = %s AND m.created_at < %s
                    """, (user_id, cutoff))
                    cursor.execute("DELETE FROM chats WHERE user_id = %s AND created_at < %s", (user_id, cutoff))
                    # delete user_files older than cutoff
                    cursor.execute("SELECT id, filepath FROM user_files WHERE user_id = %s AND uploaded_at < %s", (user_id, cutoff))
                    frows = cursor.fetchall()
                    for fr in frows:
                        try:
                            fp = fr.get('filepath')
                            if fp and os.path.exists(fp):
                                os.remove(fp)
                        except Exception:
                            logger.exception("error deleting user file during auto-delete")
                        cursor.execute("DELETE FROM user_files WHERE id = %s", (fr['id'],))
                    db.commit()
                cursor.close()
                db.close()
            except Exception:
                logger.exception("Auto-delete worker encountered an error")
            time.sleep(interval_seconds)
    t = threading.Thread(target=worker, daemon=True)
    t.start()

run_auto_delete_worker(interval_seconds=60)

# ----------------- Error handlers -----------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

# ----------------- PROFILE ROUTES -----------------

@app.route("/profile", methods=["GET"])
@token_required
def get_profile():
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("""
            SELECT id, email, full_name, date_of_birth, profile_picture, 
                   bio, phone, occupation, personalization_enabled, 
                   auto_delete, personalization, data_deletion_scheduled,
                   created_at, updated_at
            FROM users WHERE id = %s
        """, (request.user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Handle nullable fields gracefully
        if user.get("date_of_birth"):
            user["date_of_birth"] = (
                user["date_of_birth"].isoformat()
                if hasattr(user["date_of_birth"], "isoformat")
                else str(user["date_of_birth"])
            )

        if user.get("created_at"):
            user["created_at"] = (
                user["created_at"].isoformat()
                if hasattr(user["created_at"], "isoformat")
                else str(user["created_at"])
            )

        if user.get("updated_at"):
            user["updated_at"] = (
                user["updated_at"].isoformat()
                if hasattr(user["updated_at"], "isoformat")
                else str(user["updated_at"])
            )

        if user.get("data_deletion_scheduled"):
            user["data_deletion_scheduled"] = (
                user["data_deletion_scheduled"].isoformat()
                if hasattr(user["data_deletion_scheduled"], "isoformat")
                else str(user["data_deletion_scheduled"])
            )

        # Convert JSON string to dict if personalization exists
        if user.get("personalization"):
            try:
                user["personalization"] = (
                    json.loads(user["personalization"])
                    if isinstance(user["personalization"], str)
                    else user["personalization"]
                )
            except Exception:
                user["personalization"] = None

        # Default values if NULL
        user["profile_picture"] = user.get("profile_picture") or None
        user["bio"] = user.get("bio") or ""
        user["phone"] = user.get("phone") or ""
        user["occupation"] = user.get("occupation") or ""
        user["personalization_enabled"] = bool(user.get("personalization_enabled"))

        return jsonify(user), 200

    except Exception as e:
        logger.exception("Get profile failed")
        return jsonify({"error": "Failed to load profile data"}), 500
    

@app.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json(force=True)
        
        # Allowed fields to update
        allowed_fields = ['full_name', 'phone', 'date_of_birth', 'occupation', 'bio', 'auto_delete', 'personalization_enabled']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Build the update query dynamically
        set_clause = ", ".join([f"{field}=%s" for field in update_data.keys()])
        values = list(update_data.values())
        values.append(request.user_id)
        
        cursor.execute(f"UPDATE users SET {set_clause}, updated_at=NOW() WHERE id=%s", values)
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"message": "Profile updated successfully"})
        
    except Exception as e:
        logger.exception("Update profile failed")
        return jsonify({"error": "Failed to update profile"}), 500

@app.route("/profile/picture", methods=["POST"])
@token_required
def upload_profile_picture():
    """Upload profile picture"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Check if it's an image
    if not file.content_type.startswith('image/'):
        return jsonify({"error": "File must be an image"}), 400
    
    # Check file size (max 2MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        return jsonify({"error": "File too large (max 2MB)"}), 400
    
    try:
        # Ensure user folders exist and get paths
        user_paths = ensure_user_folders(request.user_id)
        profiles_dir = user_paths["profile"]
        
        # Generate secure filename - just profile.{ext} since it's user-specific folder
        file_extension = file.filename.split('.')[-1].lower()
        filename = f"profile.{file_extension}"
        filepath = os.path.join(profiles_dir, filename)
        
        # Remove old profile picture if exists (different extension)
        for old_file in os.listdir(profiles_dir):
            if old_file.startswith("profile."):
                try:
                    os.remove(os.path.join(profiles_dir, old_file))
                except:
                    pass
        
        # Save file
        file.save(filepath)
        
        # Update database with new path format
        public_path = f"/user_data/{request.user_id}/profile/{filename}"
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET profile_picture=%s, updated_at=NOW() WHERE id=%s", 
                      (public_path, request.user_id))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"message": "Profile picture uploaded", "profile_picture": public_path})
        
    except Exception as e:
        logger.exception("Profile picture upload failed")
        return jsonify({"error": "Failed to upload profile picture"}), 500

@app.route("/user_data/<int:user_id>/profile/<filename>")
def serve_profile_picture(user_id, filename):
    """Serve profile pictures from user_data folder"""
    try:
        # Security: sanitize filename to prevent path traversal
        safe_name = secure_filename(filename)
        if not safe_name or safe_name != filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        profiles_dir = get_user_data_path(user_id, "profile")
        filepath = os.path.join(profiles_dir, safe_name)
        
        # Ensure file exists
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
            
        return send_from_directory(profiles_dir, safe_name)
    except Exception as e:
        logger.error(f"Error serving profile picture: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route("/user_data/<int:user_id>/<subfolder>/<path:filename>")
@token_required
def serve_user_file(user_id, subfolder, filename):
    """Serve user files with authentication - users can only access their own data"""
    try:
        # Only allow users to access their own data
        if request.user_id != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Allowed subfolders
        allowed_subfolders = ["uploads", "exports", "recordings"]
        if subfolder not in allowed_subfolders:
            return jsonify({"error": "Invalid path"}), 400
        
        safe_name = secure_filename(filename)
        if not safe_name:
            return jsonify({"error": "Invalid filename"}), 400
        
        folder_path = get_user_data_path(user_id, subfolder)
        filepath = os.path.join(folder_path, safe_name)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
            
        return send_from_directory(folder_path, safe_name)
    except Exception as e:
        logger.error(f"Error serving user file: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route("/profile/password", methods=["PUT"])
@token_required
def change_password():
    try:
        data = request.get_json(force=True) or {}
        current = data.get('current_password')
        new = data.get('new_password')
        if not current or not new or len(new) < 6:
            return jsonify({"error": "Invalid input: new password must be >= 6 chars"}), 400
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (request.user_id,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row.get('password_hash', ''), current):
            cursor.close(); db.close()
            return jsonify({"error": "Current password incorrect"}), 401
        new_hash = generate_password_hash(new)
        cursor.execute("UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s", (new_hash, request.user_id))
        db.commit()
        cursor.close(); db.close()
        return jsonify({"message": "Password changed"}), 200
    except Exception:
        logger.exception("change_password failed")
        return jsonify({"error": "Failed to change password"}), 500

@app.route("/download_data", methods=["GET"])
@token_required
def download_user_data():
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        user_id = request.user_id
        out = io.BytesIO()
        z = zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()
        z.writestr("user.json", json.dumps(user_row, default=str))
        cursor.execute("SELECT * FROM chats WHERE user_id = %s", (user_id,))
        chats = cursor.fetchall()
        z.writestr("chats.json", json.dumps(chats, default=str))
        cursor.execute("""SELECT m.* FROM messages m JOIN chats c ON m.chat_id = c.id WHERE c.user_id = %s""", (user_id,))
        msgs = cursor.fetchall()
        z.writestr("messages.json", json.dumps(msgs, default=str))
        cursor.execute("SELECT * FROM user_files WHERE user_id = %s", (user_id,))
        files = cursor.fetchall()
        z.writestr("files.json", json.dumps(files, default=str))
        for f in files:
            try:
                fp = f.get('filepath')
                if fp and os.path.exists(fp) and os.path.getsize(fp) < (5 * 1024 * 1024):
                    arcname = f"uploaded_files/{os.path.basename(fp)}"
                    z.write(fp, arcname)
            except Exception:
                logger.exception("Error adding user file to export")
        z.close()
        out.seek(0)
        export_name = f"user_export_{user_id}_{int(time.time())}.zip"
        # Use new user_data folder structure
        user_paths = ensure_user_folders(user_id)
        export_path = user_paths["exports"]
        persisted_path = os.path.join(export_path, export_name)
        with open(persisted_path, "wb") as pf:
            pf.write(out.getbuffer())
        try:
            cur2 = db.cursor()
            cur2.execute("INSERT INTO data_exports (user_id, export_path) VALUES (%s, %s)", (user_id, persisted_path))
            db.commit()
            cur2.close()
        except Exception:
            # not fatal if table missing
            pass
        cursor.close()
        db.close()
        out.seek(0)
        return send_file(out, mimetype="application/zip", as_attachment=True, download_name="my_data.zip")
    except Exception:
        logger.exception("download_user_data failed")
        return jsonify({"error": "Failed to export data"}), 500

@app.route("/support", methods=["POST"])
@token_required
def create_support_ticket():
    try:
        data = request.get_json(force=True) or {}
        subject = data.get('subject')
        message = data.get('message')
        if not subject or not message:
            return jsonify({"error": "Subject and message required"}), 400
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO support_tickets (user_id, subject, message) VALUES (%s, %s, %s)", (request.user_id, subject, message))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "Support ticket submitted"}), 201
    except Exception:
        logger.exception("create_support_ticket failed")
        return jsonify({"error": "Failed to submit ticket"}), 500

@app.route("/account", methods=["DELETE"])
@token_required
def delete_account():
    try:
        import shutil
        db = get_db_connection()
        cursor = db.cursor()
        
        # Delete the entire user_data folder for this user
        user_folder = get_user_data_path(request.user_id)
        if os.path.exists(user_folder):
            try:
                shutil.rmtree(user_folder)
                logger.info(f"Deleted user data folder: {user_folder}")
            except Exception:
                logger.exception("Failed to remove user data folder on account delete")
        
        # delete user will cascade if your schema has foreign keys with ON DELETE CASCADE
        cursor.execute("DELETE FROM users WHERE id = %s", (request.user_id,))
        db.commit()
        cursor.close()
        db.close()
        with _user_data_lock:
            if request.user_id in _user_indices:
                del _user_indices[request.user_id]
        return jsonify({"message": "Account and all data deleted"}), 200
    except Exception:
        logger.exception("delete_account failed")
        return jsonify({"error": "Failed to delete account"}), 500

# ----------------- Misc routes -----------------
@app.route("/health", methods=["GET"])
def health():
    user_has_index = getattr(request, "user_id", None) in _user_indices
    return jsonify({
        "ok": True,
        "llm_client_configured": bool(client),
        "sentence_transformer_loaded": _sent_transformer is not None,
        "user_has_index": user_has_index,
        "pdf_loaded": _indexed_pdf_path if _indexed_pdf_path else None,
        "mode": "pdf_enhanced" if _faiss_index is not None else "general_ai"
    })

@app.route("/reindex", methods=["POST"])
def reindex():
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get("file_path", PDF_PATH)
        if not isinstance(file_path, str) or not file_path:
            return jsonify({"error": "file_path must be a non-empty string"}), 400
        if not os.path.exists(file_path):
            return jsonify({"error": f"file not found: {file_path}"}), 404
        index, paragraphs, embeddings = build_index_from_file(file_path)
        global _sent_transformer, _faiss_index, _paragraphs, _embeddings, _index_built_at, _indexed_pdf_path
        _faiss_index = index
        _paragraphs = paragraphs
        _embeddings = embeddings
        try:
            _sent_transformer = SentenceTransformer(MODEL_PATH)
        except Exception:
            logger.exception("Failed to (re)load transformer model")
        _index_built_at = time.time()
        _indexed_pdf_path = os.path.abspath(file_path)
        return jsonify({"ok": True, "message": f"Reindexed file: {file_path}", "indexed_file_path": _indexed_pdf_path})
    except Exception:
        logger.exception("Reindex failed")
        return jsonify({"error": "Reindex failed"}), 500

# ----------------- Auth / Register / Login / OTP -----------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip()
        date_of_birth = data.get("date_of_birth")
        
        logger.info(f"Registration attempt for email: {email}")

        if not email or not password or not full_name:
            logger.warning(f"Registration failed - missing fields for email: {email}")
            return jsonify({"error": "Please provide email, password, and full name"}), 400
        
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        # Check if user already exists
        cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # If user exists and is already verified, reject
            if existing_user['is_verified']:
                cursor.close()
                db.close()
                logger.warning(f"Registration failed - email already registered and verified: {email}")
                return jsonify({"error": "Email already registered. Please login."}), 409
            
            # If user exists but NOT verified, resend OTP (help them complete registration)
            else:
                cursor.close()
                db.close()
                logger.info(f"User {email} exists but not verified. Resending OTP...")
                
                try:
                    otp_code = generate_otp(email)
                    logger.info(f"OTP {otp_code} resent to unverified user: {email}")
                    return jsonify({
                        "message": "Account found but not verified. A new OTP has been sent to your email.",
                        "action": "verify"
                    }), 200
                except Exception as e:
                    logger.error(f"Failed to resend OTP for unverified user {email}: {str(e)}")
                    return jsonify({"error": "Failed to send verification email. Please try again."}), 500

        # HASH the password before storing
        password_hash = generate_password_hash(password)

        # Register user but mark as not verified
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name, date_of_birth, is_verified) VALUES (%s, %s, %s, %s, 0)",
            (email, password_hash, full_name, date_of_birth),
        )
        user_id = cursor.lastrowid
        db.commit()  # Commit user creation
        cursor.close()
        db.close()
        logger.info(f"User registered successfully with ID {user_id}: {email}")
        
        # Generate and send OTP (this function handles both DB storage and email sending)
        try:
            otp_code = generate_otp(email)
            logger.info(f"OTP {otp_code} generated and sent to {email}")
            return jsonify({"message": "Registration successful. Please verify your email with the OTP sent."}), 201
        except Exception as e:
            logger.error(f"Failed to generate/send OTP for {email}: {str(e)}")
            # User is created but OTP failed - they can request resend
            return jsonify({"message": "Registration successful but OTP sending failed. Please use 'Resend OTP'."}), 201
    except Exception as e:
        logger.exception(f"Registration failed for {email}: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email'); password = data.get('password')
        logger.info(f"Login attempt for email: {email}")
        if not email or not password:
            logger.warning(f"Login failed for {email}: Missing email or password")
            return jsonify({"error": "Missing email or password"}), 400
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, email, password_hash, full_name, is_verified FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close(); db.close()
        if not user or not check_password_hash(user.get("password_hash", ""), password):
            logger.warning(f"Login failed for {email}: Invalid credentials")
            return jsonify({"error": "Invalid credentials"}), 401
        if not user.get("is_verified"):
            logger.warning(f"Login failed for {email}: Account not verified")
            return jsonify({
                "error": "Account not verified. Please check your email for the OTP code.",
                "action": "verify",
                "message": "Don't have the OTP? Use 'Resend OTP' button."
            }), 403
        token = jwt.encode({'user_id': user['id'], 'exp': int(time.time()) + 86400}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.info(f"Login successful for user_id: {user['id']} ({email})")
        return jsonify({"message": "Login successful", "token": token, "user_id": user['id'], "email": user['email'], "full_name": user['full_name']}), 200
    except Exception:
        logger.exception(f"Login failed for email: {email}")
        return jsonify({"error": "Login failed"}), 500

@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        logger.info(f"Resend OTP request for email: {email}")
        if not email:
            logger.warning("Resend OTP failed: Email is required")
            return jsonify({"error": "Email is required"}), 400
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            cursor.close(); db.close()
            logger.warning(f"Resend OTP failed for {email}: User not found")
            return jsonify({"error": "User not found"}), 404
        if user.get("is_verified"):
            cursor.close(); db.close()
            logger.warning(f"Resend OTP failed for {email}: User is already verified")
            return jsonify({"error": "User is already verified"}), 400
        
        cursor.close()
        db.close()
        
        # Generate and send OTP (this function handles both DB storage and email sending)
        try:
            otp_code = generate_otp(email)
            logger.info(f"OTP {otp_code} resent successfully to {email}")
            return jsonify({"message": "OTP resent successfully"}), 200
        except Exception as e:
            logger.exception(f"Failed to resend OTP to {email}: {str(e)}")
            return jsonify({"error": "Failed to send OTP email"}), 500
    except Exception as e:
        logger.exception(f"Resend OTP failed for {email}: {str(e)}")
        return jsonify({"error": "Failed to resend OTP"}), 500

@app.route("/verify_otp", methods=["POST"])
def verify_otp_route():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        otp = data.get("otp")
        logger.info(f"OTP verification attempt for email: {email}, OTP: {otp}")
        
        if not email or not otp:
            logger.warning("OTP verification failed: Email and OTP are required")
            return jsonify({"error": "Email and OTP are required"}), 400
        
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        
        # Get the MOST RECENT OTP for this email that hasn't expired
        cursor.execute(
            """SELECT id, otp_code, expires_at, created_at 
               FROM otp_tokens 
               WHERE email = %s AND expires_at > NOW() 
               ORDER BY created_at DESC 
               LIMIT 1""",
            (email,)
        )
        otp_record = cursor.fetchone()
        
        if not otp_record:
            cursor.close()
            db.close()
            logger.warning(f"OTP verification failed for {email}: No valid OTP found in database")
            return jsonify({"error": "Invalid or expired OTP. Please request a new one."}), 400
        
        # Log what we found for debugging
        logger.info(f"Found OTP record for {email}: code={otp_record['otp_code']}, created={otp_record['created_at']}")
        
        # Compare OTP codes (as strings to avoid type issues)
        if str(otp_record['otp_code']).strip() != str(otp).strip():
            cursor.close()
            db.close()
            logger.warning(f"OTP verification failed for {email}: Code mismatch. Expected {otp_record['otp_code']}, got {otp}")
            return jsonify({"error": "Invalid OTP code. Please check and try again."}), 400
        
        # OTP is valid! Mark user as verified
        cursor.execute("UPDATE users SET is_verified = 1 WHERE email = %s", (email,))
        
        # Delete ALL OTPs for this email (cleanup)
        cursor.execute("DELETE FROM otp_tokens WHERE email = %s", (email,))
        
        db.commit()
        cursor.close()
        db.close()
        logger.info(f"OTP verified successfully for {email}. User account activated.")
        return jsonify({"message": "Email verified successfully. You can now login!"}), 200
        
    except Exception as e:
        logger.exception(f"OTP verification failed: {str(e)}")
        return jsonify({"error": "OTP verification failed"}), 500

# ----------------- Voice Recording & Speech-to-Text -----------------

ALLOWED_AUDIO_EXT = {'wav', 'mp3', 'ogg', 'webm', 'm4a', 'flac'}
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB for audio

@app.route("/upload_voice", methods=["POST"])
@token_required
def upload_voice_recording():
    """Upload a voice recording and transcribe it to text"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['file']
        if not file or file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        # Check extension
        file_extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_extension not in ALLOWED_AUDIO_EXT:
            return jsonify({"error": f"Audio type not allowed. Allowed: {', '.join(ALLOWED_AUDIO_EXT)}"}), 400
        
        # Size check
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > MAX_AUDIO_SIZE:
            return jsonify({"error": "Audio file too large (max 25MB)"}), 400
        
        # Ensure user folders exist
        user_paths = ensure_user_folders(request.user_id)
        recordings_dir = user_paths["recordings"]
        
        # Save with timestamp
        from datetime import datetime as dt
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.{file_extension}"
        filepath = os.path.join(recordings_dir, filename)
        file.save(filepath)
        
        # Try to transcribe using OpenAI Whisper API
        transcription = ""
        language = "unknown"
        if client:
            try:
                with open(filepath, "rb") as audio_file:
                    # Use Whisper API for transcription
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                    transcription = transcript_response.text
                    language = getattr(transcript_response, 'language', 'en')
                    logger.info(f"Transcribed audio for user {request.user_id}: {len(transcription)} chars, language: {language}")
            except Exception as e:
                logger.exception(f"Whisper transcription failed: {e}")
                transcription = ""
        
        result = {
            "message": "Voice recording uploaded successfully",
            "filename": filename,
            "filepath": f"/user_data/{request.user_id}/recordings/{filename}",
            "transcription": transcription,
            "detected_language": language,
            "file_size": file_length
        }
        
        return jsonify(result), 200
        
    except Exception:
        logger.exception("Voice recording upload failed")
        return jsonify({"error": "Failed to upload voice recording"}), 500

@app.route("/voice_chat", methods=["POST"])
@token_required
def voice_chat():
    """
    Voice-to-AI chat: Upload an audio file, transcribe it, send to AI, and return response.
    This enables real-time voice interaction with the AI.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['file']
        chat_id = request.form.get('chat_id')
        use_pdf_context = request.form.get('use_pdf_context', 'true').lower() == 'true'
        
        if not file or file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        # Check extension
        file_extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_extension not in ALLOWED_AUDIO_EXT:
            return jsonify({"error": "Audio type not allowed"}), 400
        
        # Save temporarily
        user_paths = ensure_user_folders(request.user_id)
        from datetime import datetime as dt
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_query_{timestamp}.{file_extension}"
        filepath = os.path.join(user_paths["recordings"], filename)
        file.save(filepath)
        
        # Transcribe
        if not client:
            return jsonify({"error": "AI service not configured"}), 503
        
        transcription = ""
        try:
            with open(filepath, "rb") as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcription = transcript_response.text
        except Exception as e:
            logger.exception(f"Voice chat transcription failed: {e}")
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
        if not transcription.strip():
            return jsonify({"error": "Could not understand the audio. Please speak clearly."}), 400
        
        # Now process as a regular chat query
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        
        # Create or get chat
        if not chat_id:
            cursor.execute("INSERT INTO chats (user_id, title) VALUES (%s, %s)", (request.user_id, "Voice Chat"))
            chat_id = cursor.lastrowid
            is_new_chat = True
        else:
            is_new_chat = False
        
        # Save user message
        cursor.execute("INSERT INTO messages (chat_id, sender, text) VALUES (%s, %s, %s)", 
                      (chat_id, "user", f"[Voice] {transcription}"))
        db.commit()
        
        # Get context if available
        context = "You are a helpful AI assistant."
        with _user_data_lock:
            if request.user_id in _user_indices:
                relevant = search_relevant_paragraphs_for_user(request.user_id, transcription, top_k=TOP_K)
                if relevant:
                    context = "\n\n".join(relevant)[:MAX_CONTEXT_CHARS]
        
        # Get AI response
        answer = ask_model(context, transcription, client, LLM_MODEL_NAME)
        
        # Save AI response
        cursor.execute("INSERT INTO messages (chat_id, sender, text) VALUES (%s, %s, %s)", 
                      (chat_id, "ai", answer))
        
        # Generate title for new chats
        chat_title = None
        if is_new_chat:
            chat_title = generate_chat_title(transcription, answer)
            cursor.execute("UPDATE chats SET title = %s WHERE id = %s", (chat_title, chat_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({
            "transcription": transcription,
            "answer": answer,
            "chat_id": chat_id,
            "chat_title": chat_title,
            "voice_file": f"/user_data/{request.user_id}/recordings/{filename}"
        }), 200
        
    except Exception:
        logger.exception("Voice chat failed")
        return jsonify({"error": "Voice chat failed"}), 500

# ----------------- File upload / indexing -----------------

#upload file with image recognition and OCR
@app.route("/upload_file", methods=["POST"])
@token_required
def upload_file():
    try:
        logger.info(f"File upload attempt for user {request.user_id}")
        if 'file' not in request.files:
            logger.warning(f"File upload failed for user {request.user_id}: No file part")
            return jsonify({"error": "No file part (key 'file')"}), 400
        file = request.files['file']
        if not file or file.filename == "":
            logger.warning(f"File upload failed for user {request.user_id}: No selected file")
            return jsonify({"error": "No selected file"}), 400
        if not allowed_file(file.filename):
            logger.warning(f"File upload failed for user {request.user_id}: File type not allowed for {file.filename}")
            return jsonify({"error": "File type not allowed"}), 400

        # size check
        if request.content_length and request.content_length > MAX_FILE_SIZE + 2048:
            logger.warning(f"File upload failed for user {request.user_id}: File too large (content_length)")
            return jsonify({"error": "File too large"}), 400
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > MAX_FILE_SIZE:
            logger.warning(f"File upload failed for user {request.user_id}: File too large ({file_length} bytes)")
            return jsonify({"error": "File too large"}), 400

        # Use new user_data folder structure
        user_paths = ensure_user_folders(request.user_id)
        user_upload_dir = user_paths["uploads"]
        filename = secure_filename(file.filename)
        filepath = os.path.join(user_upload_dir, filename)
        file.save(filepath)
        logger.info(f"File '{filename}' saved to '{filepath}' for user {request.user_id}")

        file_extension = filename.split('.')[-1].lower()
        meta = {"file_path": os.path.abspath(filepath), "file_type": file_extension, "built_at": time.time()}

        extracted_text = ""
        image_description = ""
        paragraphs = []

        # If it's an image -> OCR + description
        if file_extension in ALLOWED_IMAGE_EXT:
            logger.info(f"Processing image file '{filename}' for user {request.user_id}")
            extracted_text = extract_text_from_image(filepath)  # FIXED: Now uses your VisionHandler
            try:
                image_description = describe_image(filepath)
            except Exception:
                logger.exception(f"Failed to describe image '{filename}' for user {request.user_id}")
                image_description = ""
            # prefer OCR text for paragraphs, but include description always
            if extracted_text:
            # include OCR text and an AI-generated description paragraph
                paragraphs = [p for p in ((extracted_text + "\n\n" + image_description).split("\n\n")) if p.strip()]
            elif image_description:
                paragraphs = [image_description]
            else:
                paragraphs = [f"Image uploaded: {filename}"]
            # build index from these paragraphs (do not raise if OCR empty)
            embeddings, _ = embed_paragraphs(paragraphs, MODEL_PATH)
            index = create_faiss_index(embeddings)
            # keep in-memory for user
            with _user_data_lock:
                _user_indices.setdefault(request.user_id, {})
                _user_indices[request.user_id]["index"] = index
                _user_indices[request.user_id]["paragraphs"] = paragraphs
                _user_indices[request.user_id]["embeddings"] = embeddings
                _user_indices[request.user_id]["index_built_at"] = time.time()
                _user_indices[request.user_id]["file_path"] = os.path.abspath(filepath)

            # persist user-specific index+paragraphs in user_data folder
            user_index_path = os.path.join(get_user_data_path(request.user_id, "indexes"), "faiss_index.bin")
            user_paragraphs_path = os.path.join(get_user_data_path(request.user_id, "paragraphs"), "paragraphs.pkl")
            user_meta_path = f"{user_index_path}.meta.pkl"
            persist_index_and_paragraphs(index, paragraphs, user_index_path, user_paragraphs_path, user_meta_path, meta)
            logger.info(f"Image '{filename}' indexed for user {request.user_id}. OCR text length: {len(extracted_text)}, Description length: {len(image_description)}")

        else:
            # Non-image -> existing pipeline (pdf/txt/docx etc.)
            logger.info(f"Processing non-image file '{filename}' for user {request.user_id}")
            # reuse build_index_for_user semantics but avoid raising on images earlier
            try:
                index, paragraphs, embeddings = build_index_for_user(request.user_id, filepath)
                # persist user index in user_data folder
                user_index_path = os.path.join(get_user_data_path(request.user_id, "indexes"), "faiss_index.bin")
                user_paragraphs_path = os.path.join(get_user_data_path(request.user_id, "paragraphs"), "paragraphs.pkl")
                user_meta_path = f"{user_index_path}.meta.pkl"
                persist_index_and_paragraphs(index, paragraphs, user_index_path, user_paragraphs_path, user_meta_path, meta)
                logger.info(f"File '{filename}' indexed for user {request.user_id}. {len(paragraphs)} paragraphs extracted.")
            except RuntimeError as e:
                # maintain behavior: if no text extracted from non-image we raise
                logger.warning(f"Non-image file '{filename}' for user {request.user_id}: no text extracted. Error: {e}")
                return jsonify({"error": "No text extracted from file"}), 400

        # store record in DB
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO user_files (user_id, filename, filepath, file_type, uploaded_at) VALUES (%s, %s, %s, %s, NOW())",
                       (request.user_id, filename, filepath, file_extension))
        db.commit()
        cursor.close(); db.close()
        logger.info(f"File '{filename}' record saved to DB for user {request.user_id}")

        result = {
            "message": "File uploaded successfully",
            "filename": filename,
            "filepath": filepath,
            "file_type": file_extension,
            "extracted_text": extracted_text,
            "image_description": image_description
        }
        return jsonify(result), 200
    except Exception:
        logger.exception(f"File upload failed for user {request.user_id}")
        return jsonify({"error": "File upload failed"}), 500

# ----------------- Chats / messages / ask -----------------
@app.route("/chats", methods=["GET"])
@token_required
def get_chats():
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, title, created_at, updated_at FROM chats WHERE user_id = %s ORDER BY created_at DESC", (request.user_id,))
        chats = cursor.fetchall()
        cursor.close(); db.close()
        return jsonify({"chats": chats})
    except Exception:
        logger.exception("Failed to get chats")
        return jsonify({"error": "Failed to get chats"}), 500

@app.route("/chats", methods=["DELETE"])
@token_required
def delete_all_chats():
    """Delete all chats and their messages for the authenticated user"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        # Delete all messages for user's chats
        cursor.execute("""
            DELETE m FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE c.user_id = %s
        """, (request.user_id,))
        # Delete all chats for user
        cursor.execute("DELETE FROM chats WHERE user_id = %s", (request.user_id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "All chats deleted successfully"}), 200
    except Exception:
        logger.exception("Failed to delete all chats")
        return jsonify({"error": "Failed to delete chats"}), 500

@app.route("/delete_chat/<int:chat_id>", methods=["DELETE"])
@token_required
def delete_chat(chat_id):
    """Delete a specific chat and its messages"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        # Verify chat belongs to user
        cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, request.user_id))
        if not cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({"error": "Chat not found"}), 404
        # Delete messages
        cursor.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))
        # Delete chat
        cursor.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "Chat deleted successfully"}), 200
    except Exception:
        logger.exception("Failed to delete chat")
        return jsonify({"error": "Failed to delete chat"}), 500


@app.route("/get_messages/<int:chat_id>", methods=["GET"])
@token_required
def get_messages(chat_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, request.user_id))
        if not cursor.fetchone():
            cursor.close(); db.close()
            return jsonify({"error": "Chat not found for this user"}), 403
        cursor.execute("SELECT id, sender, text, context_type, created_at FROM messages WHERE chat_id = %s ORDER BY created_at ASC", (chat_id,))
        messages = cursor.fetchall()
        cursor.close(); db.close()
        return jsonify(messages)
    except Exception:
        logger.exception("Get messages failed")
        return jsonify({"error": "Failed to get messages"}), 500

@app.route("/user_pdfs", methods=["GET"])
@token_required
def get_user_pdfs():
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, filename, uploaded_at FROM user_files WHERE user_id = %s ORDER BY uploaded_at DESC", (request.user_id,))
        pdfs = cursor.fetchall()
        cursor.close(); db.close()
        return jsonify({"pdfs": pdfs})
    except Exception:
        logger.exception("Failed to get user PDFs")
        return jsonify({"error": "Failed to get user PDFs"}), 500
    

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["image"]
    path = "temp.png"
    file.save(path)

    ocr_text = vh.extract_text(path)
    caption = vh.describe_image(path)

    return jsonify({"ocr_text": ocr_text, "caption": caption})


@app.route("/ask", methods=["POST"])
@token_optional  # Changed from @token_required to support guest mode
def answer_question():
    try:
        data = request.get_json(force=True) or {}
        query = data.get("query", "").strip()
        chat_id = data.get("chat_id", "")
        use_pdf_context = data.get("use_pdf_context", True)
        stream = data.get("stream", False)

        if not query:
            return jsonify({"error": "Query missing"}), 400

        # Capture user_id safely for use in closures/generators
        current_user_id = getattr(request, 'user_id', None)

        # Guest Mode: Simple response without RAG or database persistence
        if request.is_guest:
            logger.info("Guest mode query: %s (stream=%s)", query, stream)
            try:
                # Check if LLM client is available
                if not client:
                    return jsonify({"error": "AI service temporarily unavailable"}), 503
                
                # Simple prompt for guests (no file context)
                context = "You are a helpful AI assistant. Answer this question concisely."
                
                if stream:
                    # Streaming response for guests
                    def guest_stream_generator():
                        try:
                            gen = ask_model(context, query, client, LLM_MODEL_NAME, stream=True)
                            for chunk in gen:
                                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                            yield f"data: {json.dumps({'done': True, 'is_guest': True, 'context_type': 'general'})}\n\n"
                        except Exception as e:
                            yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
                    return Response(guest_stream_generator(), content_type='text/event-stream')
                else:
                    # Non-streaming response for guests
                    ai_response = ask_model(context, query, client, LLM_MODEL_NAME, stream=False)
                    
                    return jsonify({
                        "answer": ai_response,
                        "is_guest": True,
                        "chat_id": None,
                        "context_type": "general",
                        "message": "You're using guest mode. Register to unlock file uploads, voice AI, and history!"
                    })
            except Exception as e:
                logger.error(f"Guest mode error: {e}", exc_info=True)
                return jsonify({"error": f"Failed to process query: {str(e)}"}), 500

        # Regular authenticated user flow continues below
        db = get_db_connection()
        cursor = db.cursor()

        # Fetch user's personalization and include it in context prefix (if present)
        personalization_prefix = ""
        try:
            cursor.execute("SELECT personalization FROM users WHERE id = %s", (request.user_id,))
            p = cursor.fetchone()
            if p and p.get('personalization'):
                try:
                    personalization = json.loads(p['personalization']) if isinstance(p['personalization'], str) else p['personalization']
                    parts = []
                    if personalization.get('name'): parts.append(f"Name: {personalization.get('name')}")
                    if personalization.get('occupation'): parts.append(f"Occupation: {personalization.get('occupation')}")
                    if parts:
                        personalization_prefix = "User personalization:\n" + "\n".join(parts) + "\n\n"
                except Exception:
                    pass
        except Exception:
            # ignore personalization errors
            pass

        # ensure chat exists or create it
        is_new_chat = False
        if not chat_id:
            cursor.execute("INSERT INTO chats (user_id, title) VALUES (%s, %s)", (request.user_id, "New Chat"))
            db.commit()
            chat_id = cursor.lastrowid
            is_new_chat = True
        else:
            cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, request.user_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO chats (user_id, title) VALUES (%s, %s)", (request.user_id, "New Chat"))
                db.commit()
                chat_id = cursor.lastrowid
                is_new_chat = True
            else:
                # Check if this is the first message in an existing chat
                cursor.execute("SELECT COUNT(*) as cnt FROM messages WHERE chat_id = %s", (chat_id,))
                msg_count = cursor.fetchone()
                if msg_count and msg_count[0] == 0:
                    is_new_chat = True

        # Save user message
        cursor.execute("INSERT INTO messages (chat_id, sender, text) VALUES (%s, %s, %s)", (chat_id, "user", query))
        db.commit()
        user_message_id = cursor.lastrowid



        # get or build per-user index if available
        with _user_data_lock:
            user_has_index = request.user_id in _user_indices
            if user_has_index:
                user_data = _user_indices[request.user_id]
                index = user_data.get("index")
                paragraphs = user_data.get("paragraphs")
                file_path = user_data.get("file_path", "")
            else:
                index = paragraphs = file_path = None

        # attempt to load persisted index if not present (from new user_data folder)
        if not user_has_index:
            faiss_path = os.path.join(get_user_data_path(request.user_id, "indexes"), "faiss_index.bin")
            paragraphs_path = os.path.join(get_user_data_path(request.user_id, "paragraphs"), "paragraphs.pkl")
            meta_path = f"{faiss_path}.meta.pkl"
            cursor.execute("SELECT filepath FROM user_files WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT 1", (request.user_id,))
            row = cursor.fetchone()
            expected_file_path = row[0] if row else None
            if expected_file_path and os.path.exists(faiss_path) and os.path.exists(paragraphs_path) and os.path.exists(meta_path):
                loaded = load_index_and_paragraphs(faiss_path, paragraphs_path, meta_path, expected_file_path)
                if loaded[0] is not None:
                    index, paragraphs, meta = loaded
                    file_path = meta.get("file_path", "") if meta else None
                    with _user_data_lock:
                        _user_indices[request.user_id] = {"index": index, "paragraphs": paragraphs, "file_path": file_path, "index_built_at": time.time()}
                    logger.info("Loaded user-specific index from disk for user %s", request.user_id)
                else:
                    logger.info("User-specific FAISS index exists but did not match uploaded file; rebuilding recommended.")

        # ENHANCED: Classify query and choose context intelligently
        query_intent = classify_query(query, has_documents=(index is not None and paragraphs))
        logger.info(f"Query classified as: {query_intent['type']}")
        
        # Handle different query types
        if query_intent['type'] == 'page_specific' and query_intent.get('page_number'):
            # Page-specific query - get content from that page
            page_num = query_intent['page_number']
            page_content = get_page_content(request.user_id, page_num)
            if page_content and not page_content.startswith("No content found"):
                combined_context = personalization_prefix + f"Content from page {page_num}:\n\n{page_content[:MAX_CONTEXT_CHARS]}"
                context_type = "file"
            else:
                combined_context = personalization_prefix + f"No content found on page {page_num}. The document may not have that many pages."
                context_type = "general"
        
        elif query_intent['type'] == 'analytical' and query_intent.get('analysis_type') == 'word_count':
            # Word count query
            target_word = query_intent.get('target_word', '')
            if paragraphs:
                result = count_word_frequency(paragraphs, target_word)
                # Build detailed response context
                page_breakdown = ""
                if result.get('pages'):
                    page_details = [f"Page {p}: {c} occurrences" for p, c in list(result['pages'].items())[:10]]
                    page_breakdown = ". Page breakdown: " + "; ".join(page_details)
                    if len(result['pages']) > 10:
                        page_breakdown += f"... and {len(result['pages']) - 10} more pages"
                combined_context = personalization_prefix + f"WORD COUNT ANALYSIS RESULT: The word '{target_word}' appears exactly {result['total']} times in the document, found across {result.get('page_count', 0)} different pages{page_breakdown}. Provide this exact count to the user."
                context_type = "file"
            else:
                combined_context = personalization_prefix + "No documents uploaded for analysis."
                context_type = "general"
        
        elif query_intent['type'] == 'analytical' and query_intent.get('analysis_type') == 'keyword_extraction':
            # Keyword extraction query
            if paragraphs:
                full_text = ' '.join([p.get('text', '') if isinstance(p, dict) else p for p in paragraphs])
                keywords_result = extract_keywords(full_text, method='auto', top_n=20)
                kw_list = [kw.get('keyword', '') for kw in keywords_result[:15]]
                combined_context = personalization_prefix + f"Top keywords extracted: {', '.join(kw_list)}"
                context_type = "file"
            else:
                combined_context = personalization_prefix + "No documents uploaded for keyword extraction."
                context_type = "general"
        
        elif query_intent['type'] == 'real_time_info':
            # Real-time information query (weather, Wikipedia)
            # Check if query contains weather-related keywords (flexible matching)
            import re
            if re.search(r'weath\w*|temp\w*|climat\w*', query, re.IGNORECASE):
                # Extract location from query - handle multi-word locations with commas
                # Match ANY weather-related word + in/at/for + location
                location_match = re.search(r'(?:weath\w*|temp\w*|climat\w*)\s+(?:in|at|for)\s+([\w\s,]+?)(?:\?|$)', query, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).strip()
                else:
                    # Fallback: look for "in <location>" pattern anywhere in query
                    fallback_match = re.search(r'\s+(?:in|at)\s+([\w\s,]+?)(?:\?|$)', query, re.IGNORECASE)
                    if fallback_match:
                        location = fallback_match.group(1).strip()
                    else:
                        location = 'unknown'
                
                logger.info(f"Extracted location: {location}")
                weather_data = get_weather(location)
                logger.info(f"Weather API response: {weather_data}")  # DEBUG: See what API returns
                
                if weather_data.get('success'):
                    combined_context = personalization_prefix + f"Current weather in {weather_data.get('location', location)}: {weather_data.get('temperature')}°C, {weather_data.get('description')}. Humidity: {weather_data.get('humidity')}%"
                    logger.info(f"Weather context set successfully")
                else:
                    logger.warning(f"Weather API failed: {weather_data.get('error')} - {weather_data.get('description')}")
                    combined_context = personalization_prefix + f"Could not fetch weather data: {weather_data.get('description')}"
                context_type = "real_time"
            else:
                # Try Wikipedia
                wiki_result = search_wikipedia(query)
                if wiki_result.get('success'):
                    combined_context = personalization_prefix + f"From Wikipedia:\n\n{wiki_result.get('summary', '')}"
                    context_type = "real_time"
                else:
                    combined_context = personalization_prefix + "Could not fetch real-time information."
                    context_type = "general"
        
        elif use_pdf_context and index is not None and paragraphs:
            # Standard RAG query
            relevant = search_relevant_paragraphs_for_user(request.user_id, query, top_k=TOP_K)
            if relevant:
                # Handle both dict (new format) and string (old format)
                relevant_texts = [r.get('text', r) if isinstance(r, dict) else r for r in relevant]
                combined_context = personalization_prefix + ("\n\n".join(relevant_texts)[:MAX_CONTEXT_CHARS])
                context_type = "file"
            else:
                combined_context = personalization_prefix + "You are a helpful AI assistant. Answer based on general knowledge."
                context_type = "general"
        else:
            combined_context = personalization_prefix + "You are a helpful AI assistant. Answer based on general knowledge."
            context_type = "general"

        if stream:
            # Streaming response
            def stream_generator():
                full_answer = ""
                file_basename = os.path.basename(file_path) if file_path else None
                chat_title = None
                try:
                    gen = ask_model(combined_context, query, client, LLM_MODEL_NAME, stream=True)
                    for chunk in gen:
                        full_answer += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
                    # Generate title for new chats after we have the full answer
                    if is_new_chat and full_answer:
                        chat_title = generate_chat_title(query, full_answer)
                    
                    # Save full AI response BEFORE sending done signal so we can get ID
                    db_stream = get_db_connection()
                    cursor_stream = db_stream.cursor()
                    cursor_stream.execute("INSERT INTO messages (chat_id, sender, text, context_type) VALUES (%s, %s, %s, %s)",
                                          (chat_id, "ai", full_answer, context_type))
                    message_id = cursor_stream.lastrowid
                    
                    # Update chat title if this is a new chat
                    if is_new_chat and chat_title:
                        cursor_stream.execute("UPDATE chats SET title = %s WHERE id = %s", (chat_title, chat_id))
                    
                    # Save to query history
                    try:
                        save_query_to_history(
                            db_stream,
                            current_user_id,
                            query,
                            full_answer,
                            context={'type': context_type},
                            intent=query_intent.get('type')
                        )
                    except Exception as e:
                        logger.error(f"Failed to save query history (stream): {e}")

                    db_stream.commit()
                    cursor_stream.close()
                    db_stream.close()

                    yield f"data: {json.dumps({'done': True, 'chat_id': chat_id, 'message_id': message_id, 'user_message_id': user_message_id, 'context_type': context_type, 'file': file_basename, 'chat_title': chat_title})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"


            return Response(stream_generator(), mimetype='text/event-stream')
        else:
            # Non-streaming
            answer = ask_model(combined_context, query, client, LLM_MODEL_NAME)
            cursor.execute("INSERT INTO messages (chat_id, sender, text, context_type) VALUES (%s, %s, %s, %s)", (chat_id, "ai", answer, context_type))
            message_id = cursor.lastrowid
            
            chat_title = None
            if is_new_chat:
                chat_title = generate_chat_title(query, answer)
                cursor.execute("UPDATE chats SET title = %s WHERE id = %s", (chat_title, chat_id))
            
            # Save to query history
            try:
                save_query_to_history(
                    db,
                    current_user_id,
                    query,
                    answer,
                    context={'type': context_type},
                    intent=query_intent.get('type')
                )
            except Exception as e:
                logger.error(f"Failed to save query history (non-stream): {e}")

            db.commit()
            cursor.close()
            db.close()
            
            return jsonify({
                'answer': answer, 
                'chat_id': chat_id, 
                'message_id': message_id,
                'user_message_id': user_message_id,
                'context_type': context_type,
                'chat_title': chat_title
            })

    except Exception:
        logger.exception("Ask failed")
        return jsonify({"error": "Ask failed"}), 500
    




# ----------------- Week 3: Advanced Features Endpoints -----------------

@app.route("/count_words", methods=["POST"])
@token_required
def count_words_endpoint():
    """Count word occurrences in user's documents"""
    try:
        data = request.get_json(force=True) or {}
        word = data.get('word', '').strip()
        case_sensitive = data.get('case_sensitive', False)
        
        if not word:
            return jsonify({'error': 'Word parameter required'}), 400
        
        # Get user's document chunks
        with _user_data_lock:
            user_data = _user_indices.get(request.user_id)
        
        if not user_data or not user_data.get('paragraphs'):
            return jsonify({'error': 'No documents uploaded'}), 404
        
        chunks = user_data.get('paragraphs', [])
        
        # Count occurrences
        result = count_word_frequency(chunks, word, case_sensitive)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.exception(f"Word counting failed: {e}")
        return jsonify({'error': 'Word counting failed'}), 500


@app.route("/extract_keywords", methods=["POST"])
@token_required
def extract_keywords_endpoint():
    """Extract keywords from user's documents"""
    try:
        data = request.get_json(force=True) or {}
        method = data.get('method', 'auto')  # yake, rake, simple, or auto
        top_n = data.get('top_n', 20)
        
        # Get user's document chunks
        with _user_data_lock:
            user_data = _user_indices.get(request.user_id)
        
        if not user_data or not user_data.get('paragraphs'):
            return jsonify({'error': 'No documents uploaded'}), 404
        
        chunks = user_data.get('paragraphs', [])
        
        # Combine all text
        full_text = ' '.join([chunk.get('text', '') if isinstance(chunk, dict) else chunk for chunk in chunks])
        
        # Extract keywords
        keywords = extract_keywords(full_text, method=method, top_n=top_n)
        
        return jsonify({
            'keywords': keywords,
            'method': keywords[0].get('method') if keywords else method,
            'total_keywords': len(keywords)
        }), 200
    
    except Exception as e:
        logger.exception(f"Keyword extraction failed: {e}")
        return jsonify({'error': 'Keyword extraction failed'}), 500


@app.route("/document_stats", methods=["GET"])
@token_required
def document_stats_endpoint():
    """Get statistics about uploaded documents"""
    try:
        # Get user's document chunks
        with _user_data_lock:
            user_data = _user_indices.get(request.user_id)
        
        if not user_data or not user_data.get('paragraphs'):
            return jsonify({'error': 'No documents uploaded'}), 404
        
        chunks = user_data.get('paragraphs', [])
        
        # Get statistics
        stats = get_document_stats(chunks)
        
        # Add file info
        stats['file_path'] = user_data.get('file_path', 'Unknown')
        stats['file_name'] = os.path.basename(stats['file_path']) if stats.get('file_path') else 'Unknown'
        stats['indexed_at'] = user_data.get('index_built_at', 0)
        
        return jsonify(stats), 200
    
    except Exception as e:
        logger.exception(f"Document stats failed: {e}")
        return jsonify({'error': 'Failed to get document statistics'}), 500


@app.route("/query_history", methods=["GET"])
@token_required
def get_query_history_endpoint():
    """Get user's query history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        intent_filter = request.args.get('intent', None)
        
        db = get_db_connection()
        history = QueryHistoryManager.get_query_history(
            db, request.user_id, limit=limit, intent_filter=intent_filter
        )
        db.close()
        
        # Convert timestamps to ISO format
        for item in history:
            if item.get('timestamp'):
                item['timestamp'] = item['timestamp'].isoformat()
        
        return jsonify({
            'history': history,
            'count': len(history)
        }), 200
    
    except Exception as e:
        logger.exception(f"Get query history failed: {e}")
        return jsonify({'error': 'Failed to get query history'}), 500


@app.route("/rerun_query/<int:query_id>", methods=["POST"])
@token_required
def rerun_query_endpoint(query_id):
    """Re-execute a historical query with current documents"""
    try:
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        
        # Get original query
        cursor.execute("""
            SELECT query_text, response_text, context_used
            FROM query_history
            WHERE id = %s AND user_id = %s
        """, (query_id, request.user_id))
        
        original = cursor.fetchone()
        
        if not original:
            cursor.close()
            db.close()
            return jsonify({'error': 'Query not found'}), 404
        
        query_text = original['query_text']
        
        # Get current user data
        with _user_data_lock:
            user_has_index = request.user_id in _user_indices
        
        # Classify and execute query (simplified)
        intent = classify_query(query_text, has_documents=user_has_index)
        
        # Execute based on intent (simplified - would use full /ask logic)
        if intent['requires_rag'] and user_has_index:
            # Search documents
            relevant = search_relevant_paragraphs_for_user(request.user_id, query_text, top_k=5)
            context = '\n\n'.join(relevant) if relevant else 'No relevant content found'
        else:
            context = 'General AI response'
        
        # Get AI response
        new_response = ask_model(context, query_text, client, LLM_MODEL_NAME)
        
        # Save rerun
        new_context = {'files': [str(request.user_id)]}  # Simplified
        rerun_result = QueryHistoryManager.rerun_query(
            db, query_id, new_response, new_context
        )
        
        db.close()
        
        return jsonify(rerun_result), 200
    
    except Exception as e:
        logger.exception(f"Rerun query failed: {e}")
        return jsonify({'error': 'Failed to rerun query'}), 500


# ----------------- Week 4: Bookmarking & Templates Endpoints -----------------

@app.route("/bookmarks", methods=["GET", "POST", "DELETE"])
@token_required
def manage_bookmarks():
    """Manage user bookmarks"""
    try:
        if request.method == "GET":
            # Get bookmarks
            tag_filter = request.args.get('tag', None)
            limit = request.args.get('limit', 100, type=int)
            
            db = get_db_connection()
            bookmarks = BookmarkManager.get_bookmarks(db, request.user_id, tag_filter, limit)
            db.close()
            
            return jsonify({
                'bookmarks': bookmarks,
                'count': len(bookmarks)
            }), 200
        
        elif request.method == "POST":
            # Create bookmark
            data = request.get_json(force=True) or {}
            message_id = data.get('message_id')
            title = data.get('title')
            tags = data.get('tags', [])
            notes = data.get('notes')
            
            if not message_id:
                return jsonify({'error': 'message_id required'}), 400
            
            db = get_db_connection()
            bookmark_id = BookmarkManager.create_bookmark(
                db, request.user_id, message_id, title, tags, notes
            )
            db.close()
            
            if bookmark_id:
                return jsonify({
                    'success': True,
                    'bookmark_id': bookmark_id,
                    'message': 'Bookmark created'
                }), 201
            else:
                return jsonify({'error': 'Failed to create bookmark'}), 500
        
        elif request.method == "DELETE":
            # Delete bookmark
            data = request.get_json(force=True) or {}
            bookmark_id = data.get('bookmark_id')
            
            if not bookmark_id:
                return jsonify({'error': 'bookmark_id required'}), 400
            
            db = get_db_connection()
            deleted = BookmarkManager.delete_bookmark(db, bookmark_id, request.user_id)
            db.close()
            
            if deleted:
                return jsonify({'success': True, 'message': 'Bookmark deleted'}), 200
            else:
                return jsonify({'error': 'Bookmark not found or already deleted'}), 404
    
    except Exception as e:
        logger.exception(f"Bookmark management failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/export_bookmarks", methods=["POST"])
@token_required
def export_bookmarks_endpoint():
    """Export bookmarks to PDF"""
    try:
        data = request.get_json(force=True) or {}
        bookmark_ids = data.get('bookmark_ids', None)  # None = all bookmarks
        
        db = get_db_connection()
        pdf_buffer = BookmarkManager.export_to_pdf(db, request.user_id, bookmark_ids)
        db.close()
        
        if not pdf_buffer:
            return jsonify({'error': 'No bookmarks to export or PDF generation failed'}), 404
        
        # Send PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'bookmarks_export_{request.user_id}.pdf'
        )
    
    except Exception as e:
        logger.exception(f"Bookmark export failed: {e}")
        return jsonify({'error': 'PDF export failed'}), 500


@app.route("/templates", methods=["GET", "POST"])
@token_required
def manage_templates():
    """Get or create templates"""
    try:
        if request.method == "GET":
            # Get templates
            category = request.args.get('category', None)
            include_system = request.args.get('include_system', 'true').lower() == 'true'
            
            db = get_db_connection()
            if include_system:
                templates = TemplateManager.get_templates(db, request.user_id, category)
            else:
                templates = TemplateManager.get_templates(db, request.user_id, category, include_public=False)
            db.close()
            
            return jsonify({
                'templates': templates,
                'count': len(templates)
            }), 200
        
        elif request.method == "POST":
            # Create custom template
            data = request.get_json(force=True) or {}
            name = data.get('name')
            template_text = data.get('template_text')
            description = data.get('description')
            category = data.get('category', 'custom')
            is_public = data.get('is_public', False)
            
            if not name or not template_text:
                return jsonify({'error': 'name and template_text required'}), 400
            
            # Extract variables
            variables = TemplateManager.extract_variables(template_text)
            
            db = get_db_connection()
            template_id = TemplateManager.create_template(
                db, request.user_id, name, template_text, description, category, variables, is_public
            )
            db.close()
            
            if template_id:
                return jsonify({
                    'success': True,
                    'template_id': template_id,
                    'variables': variables,
                    'message': 'Template created'
                }), 201
            else:
                return jsonify({'error': 'Failed to create template'}), 500
    
    except Exception as e:
        logger.exception(f"Template management failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/execute_template", methods=["POST"])
@token_required
def execute_template_endpoint():
    """Execute a template with variables and return AI response"""
    try:
        data = request.get_json(force=True) or {}
        template_id = data.get('template_id')
        variables = data.get('variables', {})
        
        if not template_id:
            return jsonify({'error': 'template_id required'}), 400
        
        # Get template
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM prompt_templates
            WHERE id = %s AND (user_id = %s OR user_id IS NULL OR is_public = TRUE)
        """, (template_id, request.user_id))
        
        template = cursor.fetchone()
        
        if not template:
            cursor.close()
            db.close()
            return jsonify({'error': 'Template not found'}), 404
        
        # Execute template (substitute variables)
        executed_query = TemplateManager.execute_template(template['template_text'], variables)
        
        # Record usage
        TemplateManager.record_usage(db, template_id, request.user_id)
        
        cursor.close()
        db.close()
        
        # Now execute as a regular query (simplified - use full /ask logic)
        with _user_data_lock:
            user_has_index = request.user_id in _user_indices
        
        if user_has_index:
            relevant = search_relevant_paragraphs_for_user(request.user_id, executed_query, top_k=5)
            context = '\n\n'.join(relevant) if relevant else 'General AI context'
        else:
            context = 'General AI context'
        
        # Get AI response
        answer = ask_model(context, executed_query, client, LLM_MODEL_NAME)
        
        return jsonify({
            'executed_query': executed_query,
            'answer': answer,
            'template_name': template['name'],
            'variables_used': variables
        }), 200
    
    except Exception as e:
        logger.exception(f"Template execution failed: {e}")
        return jsonify({'error': 'Template execution failed'}), 500


@app.route("/popular_templates", methods=["GET"])
@token_required
def popular_templates_endpoint():
    """Get most popular templates"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        db = get_db_connection()
        templates = TemplateManager.get_popular_templates(db, limit)
        db.close()
        
        return jsonify({
            'templates': templates,
            'count': len(templates)
        }), 200
    
    except Exception as e:
        logger.exception(f"Get popular templates failed: {e}")
        return jsonify({'error': 'Failed to get popular templates'}), 500


# ----------------- Week 5: Conversation Branching Endpoints -----------------

@app.route("/branches/<int:chat_id>", methods=["GET"])
@token_required
def get_conversation_branches(chat_id):
    """Get all branches for a conversation"""
    try:
        # Verify user owns this chat
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM chats WHERE id = %s AND user_id = %s
        """, (chat_id, request.user_id))
        
        chat = cursor.fetchone()
        cursor.close()
        
        if not chat:
            db.close()
            return jsonify({'error': 'Chat not found'}), 404
        
        # Get tree structure
        tree = ConversationTree.get_tree_structure(db, chat_id)
        db.close()
        
        return jsonify(tree), 200
    
    except Exception as e:
        logger.exception(f"Get branches failed: {e}")
        return jsonify({'error': 'Failed to get branches'}), 500


@app.route("/create_branch", methods=["POST"])
@token_required
def create_branch_endpoint():
    """Create a new conversation branch"""
    try:
        data = request.get_json(force=True) or {}
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        parent_message_id = data.get('parent_message_id')
        branch_name = data.get('branch_name', 'Alternative Response')
        query = data.get('query')  # New query for this branch
        
        if not chat_id or not message_id:
            return jsonify({'error': 'chat_id and message_id required'}), 400
        
        # Verify user owns this chat
        db = get_db_connection()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM chats WHERE id = %s AND user_id = %s
        """, (chat_id, request.user_id))
        
        chat = cursor.fetchone()
        
        if not chat:
            cursor.close()
            db.close()
            return jsonify({'error': 'Chat not found'}), 404
        
        # Create branch
        branch_id = ConversationTree.create_branch(
            db, chat_id, message_id, parent_message_id, branch_name
        )
        
        cursor.close()
        db.close()
        
        if branch_id:
            return jsonify({
                'success': True,
                'branch_id': branch_id,
                'message': 'Branch created',
                'branch_name': branch_name
            }), 201
        else:
            return jsonify({'error': 'Failed to create branch'}), 500
    
    except Exception as e:
        logger.exception(f"Create branch failed: {e}")
        return jsonify({'error': 'Failed to create branch'}), 500


@app.route("/compare_branches", methods=["POST"])
@token_required
def compare_branches_endpoint():
    """Compare multiple conversation branches"""
    try:
        data = request.get_json(force=True) or {}
        branch_ids = data.get('branch_ids', [])
        
        if not branch_ids or len(branch_ids) < 2:
            return jsonify({'error': 'Need at least 2 branch_ids to compare'}), 400
        
        db = get_db_connection()
        comparison = ConversationTree.compare_branches(db, branch_ids)
        db.close()
        
        if 'error' in comparison:
            return jsonify(comparison), 400
        
        return jsonify(comparison), 200
    
    except Exception as e:
        logger.exception(f"Compare branches failed: {e}")
        return jsonify({'error': 'Failed to compare branches'}), 500


@app.route("/branch_preference", methods=["POST"])
@token_required
def set_branch_preference_endpoint():
    """Set user preference for a branch (preferred/neutral/rejected)"""
    try:
        data = request.get_json(force=True) or {}
        branch_id = data.get('branch_id')
        preference = data.get('preference', 'neutral')
        quality_score = data.get('quality_score')
        
        if not branch_id:
            return jsonify({'error': 'branch_id required'}), 400
        
        db = get_db_connection()
        success = ConversationTree.set_branch_preference(
            db, branch_id, preference, quality_score
        )
        db.close()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Preference updated'
            }), 200
        else:
            return jsonify({'error': 'Failed to set preference'}), 500
    
    except Exception as e:
        logger.exception(f"Set branch preference failed: {e}")
        return jsonify({'error': 'Failed to set preference'}), 500


@app.route("/branch_path/<int:message_id>", methods=["GET"])
@token_required
def get_branch_path_endpoint(message_id):
    """Get the full conversation path to a specific message"""
    try:
        db = get_db_connection()
        path = ConversationTree.get_branch_path(db, message_id)
        db.close()
        
        return jsonify({
            'path': path,
            'length': len(path)
        }), 200
    
    except Exception as e:
        logger.exception(f"Get branch path failed: {e}")
        return jsonify({'error': 'Failed to get branch path'}), 500


# ----------------- Run -----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=True)
