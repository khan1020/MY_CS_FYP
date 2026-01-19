# AI ChatBot Project

A feature-rich Flask-based AI ChatBot with RAG capabilities, local query history, bookmarks, and real-time weather integration.

## 🚀 New Features (Jan 2026)

- **Real-Time Weather**: Integrated AccuWeather API with intelligent query detection ("temp in Dubai").
- **Bookmarks**: Save important messages, export to PDF.
- **Local History**: Browser-based history for recent queries.
- **RAG System**: Enhanced document querying with PDF/Text support.

## 🛠️ Setup Instructions

### 1. Environment Variables
Create a `.env` file (see `.env.example`) and add your API keys:

```bash
# Weather API (Get key from developer.accuweather.com)
ACCUWEATHER_API_KEY=your_key_here

# LLM Provider
OPENROUTER_API_KEY=your_key_here
```

### 2. Large Models
The `model/` directory is excluded from this repository (4.3 GB).
The system will automatically download `sentence-transformers/all-MiniLM-L6-v2` on first run if not present.

### 3. Database
Import `chatbotdb.sql` into your logical MySQL database:
```bash
mysql -u root -p chatbotdb < chatbotdb.sql
```

## 📝 Usage

run the server:
```bash
python "chat bot 3 api.py"
```
