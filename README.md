# Intelligent Document Chatbot with RAG & Vision AI

A production-ready AI chatbot featuring Retrieval-Augmented Generation (RAG), OCR/Vision capabilities, and real-time tools.

## 🌟 Features

- **Document RAG**: Chat with PDFs, DOCX, TXT files using semantic search (FAISS + BM25).
- **Vision AI**: Extract text from images (OCR) and generate captions (BLIP model).
- **Real-Time Tools**:
  - **Weather**: Live updates via AccuWeather (intelligent typo-tolerant query detection).
  - **Wikipedia**: Instant knowledge retrieval.
  - **Calculator**: Mathematical operations.
- **Smart History**: Browser-based local query history & bookmark management.
- **Authentication**: Secure JWT auth with OTP email verification.

---

## 🛠️ Prerequisites

1. **Python 3.8+**: [Download Here](https://www.python.org/downloads/)
2. **MySQL Database**: [Download XAMPP](https://www.apachefriends.org/download.html) (or standalone MySQL)
3. **Tesseract OCR (Required for Images)**:
   - **Windows**: [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to `C:\Program Files\Tesseract-OCR`
   - Add to System PATH.

---

## 📦 Installation Guide

### 1. Clone & Setup
```bash
git clone https://github.com/khan1020/MY_CS_FYP.git
cd MY_CS_FYP
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118  # Optional: For NVIDIA GPU support
```

### 4. Database Setup
1. Start MySQL (XAMPP Control Panel -> Start MySQL).
2. Create a database named `chatbotdb`.
3. Import the schema:
   ```bash
   mysql -u root -p chatbotdb < chatbotdb.sql
   ```

---

## 🔑 Environment Configuration (.env)

Create a `.env` file in the root directory. **Copy the structure below:**

```ini
# --- LLM Provider (Required) ---
OPENROUTER_API_KEY=your_openrouter_key_here

# --- Weather API (Required for Weather) ---
# Get free key from: https://developer.accuweather.com/
ACCUWEATHER_API_KEY=your_accuweather_key_here

# --- Email (Required for OTP) ---
# Use Gmail App Password (myaccount.google.com/apppasswords)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

# --- Security ---
JWT_SECRET_KEY=generate_a_long_random_string_here
FLASK_SECRET_KEY=generate_another_random_string_here

# --- Database ---
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=chatbotdb

# --- Vision & Models ---
# Path to local BLIP model (if pre-downloaded) or "Salesforce/blip-image-captioning-base"
BLIP_MODEL=Salesforce/blip-image-captioning-base
```

---

## 🧠 Handling Large Models (4.3 GB)

The `model/` folder is **excluded** from GitHub because it is too large (4.3 GB). It typically contains:
- **Sentence Transformers**: `all-MiniLM-L6-v2` (for RAG).
- **BLIP Model**: `Salesforce/blip-image-captioning-base` (for Image Captioning).

### Option A: Automatic Download (Recommended for Fresh Install)
The system is configured to download these models automatically on the first run if they are missing.
- **Note**: The code currently looks for local files properties. If you get a "model not found" error, search `vision_handler.py` and `chat bot 3 api.py` and remove `local_files_only=True` to allow downloading.

### Option B: Manual Restore (If you have the backup)
If you have the `model` folder backup:
1. Copy the `model` folder into the root of the project.
2. Ensure it follows this structure:
   ```
   model/
   ├── sentence-transformers/
   └── models--Salesforce--blip-image-captioning-base/
   ```

---

## 🚀 How to Run

1. **Start the Backend**:
   ```bash
   python "chat bot 3 api.py"
   ```
   *Wait for "Running on http://127.0.0.1:5000" and "Models loaded"*

2. **Access the App**:
   - Open command prompt/terminal.
   - Go to http://localhost/backend_latest/index.html (if getting 404, verify the XAMPP path or open `index.html` directly in browser, though some features require a server).

---

## 📚 API Architecture

### Main API (`chat bot 3 api.py`)
- `/ask`: Main chat endpoint (Streamed response).
- `/upload_file`: Processing PDFs/Docs for RAG.
- `/bookmarks`: CRUD operations for bookmarks.

### Logic Handlers
- **`query_classifier.py`**: Regex-based intent detection (Weather, Wikipedia, Files).
- **`vision_handler.py`**: Handles OCR (Tesseract) and Captioning (BLIP).
- **`free_tools.py`**: External API wrappers (AccuWeather).
- **`hybrid_retriever.py`**: Semantic (FAISS) + Keyword (BM25) search fusion.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **TesseractNotFound** | Install Tesseract and set path in System Variables or `vision_handler.py`. |
| **OSError: Can't load model** | Models are missing. Set `local_files_only=False` in code to download them, or restore `model/` folder. |
| **MySQL Connection Error** | Check if XAMPP MySQL is running and `.env` credentials are correct. |
| **Weather "No Data"** | Verify `ACCUWEATHER_API_KEY` in `.env`. Check console logs for API errors. |

---

## License
MIT License
