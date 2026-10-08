# ⚡ NEXUS AI VIDEO ASSISTANT — RAG MEETING INTELLIGENCE

> A free, local, AI-powered meeting and video intelligence assistant with native multilingual (English & Hinglish) support, LangChain LCEL orchestration, Groq LPU (Llama 3.3 70B) ultra-fast reasoning, ChromaDB RAG retrieval, and a next-generation UI.

---

## 🌟 Key Features

- **Universal Audio Ingestion**: Process YouTube URLs directly or upload local meeting files (`.mp4`, `.mp3`, `.wav`, `.m4a`, `.mov`, `.mkv`) with automatic 16kHz mono normalization and smart chunking.
- **Multilingual Speech-to-Text**:
  - **English**: Local Whisper model execution with zero API costs.
  - **Hindi & Hinglish**: High-accuracy Sarvam Saaras AI integration with direct translation to structured English.
- **Ultra-Fast Summarization**: Map-Reduce LangChain LCEL chain powered by Groq LPU (Llama 3.3 70B at 500+ tok/sec).
- **Structured Extraction Matrix**:
  - **Action Items**: Explicit task description, designated owner, deadline, and priority rating.
  - **Key Decisions**: Ratified consensus items numbered with context.
  - **Open Questions**: Unresolved topics with one-click "Ask RAG" buttons.
- **Interactive RAG Knowledge Assistant**:
  - Conversational Q&A grounded exclusively in verbatim meeting segments via dense ChromaDB vector search.
  - Pre-built suggested prompt pills for instant insights.
- **Enterprise Export Hub**:
  - 📄 Formal Executive PDF Report (`fpdf2` with clean typography and layout).
  - 📝 Markdown package (`.md` for Obsidian, Notion & GitHub).
  - 📋 Plain text summary (`.txt`).
  - 📦 Structured JSON payload (`.json` for CRM and automated workflows).
- **Interactive Showcase Demo**: Instant 1-second preview mode with pre-loaded realistic executive session data.

---

## 🚀 Quick Start

### 1. Environment Setup
Make sure your Python virtual environment is activated and dependencies are installed:
```bash
pip install -r req.txt
```

Verify your `.env` file contains your credentials:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
SARVAM_API_KEY=your_sarvam_key_here
WHISPER_MODEL=small
```

### 2. Launch the Streamlit Studio UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to access the full application with the glassmorphism theme, audio visualizers, interactive checklist, and RAG chat.

### 3. Standalone Web Frontend
You can also launch the zero-dependency web frontend located in the `frontend/` directory:
- Open `frontend/index.html` directly in any web browser, or serve it using any local static server:
```bash
python -m http.server 8000 --directory frontend
```

---

## 📁 Architecture Overview

```
AI Video Assistant/
├── app.py                   # Main Streamlit Application (Ultra-Modern Glassmorphic UI)
├── main.py                  # CLI Pipeline Orchestrator
├── core/
│   ├── transcribers.py      # Whisper & Sarvam AI STT Engine
│   ├── summarize.py         # Mistral Map-Reduce Summarizer
│   ├── extractor.py         # Action items, Decisions & Questions LCEL chains
│   ├── vector_store.py      # ChromaDB embeddings & indexing
│   └── rag_engine.py        # Conversational RAG chain
├── utils/
│   ├── audio_process.py     # yt-dlp & pydub conversion / chunking
│   ├── export_helper.py     # PDF, MD, TXT, JSON generation & parsers
│   └── demo_data.py         # Realistic demo dataset for instant UI preview
├── frontend/                # Standalone HTML5 / CSS3 / Vanilla JS Web App
│   ├── index.html           # Modern Studio Layout
│   ├── style.css            # Dark Obsidian Glassmorphism Design System
│   └── app.js               # Canvas visualizer & interactive controller
├── dowonolades/             # Local cache for audio chunks
└── req.txt                  # Python dependencies
```
