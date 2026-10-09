# 🎬 AI Video Assistant — Meeting Intelligence & Video Analytics

> An AI-powered meeting and video intelligence assistant featuring native multilingual speech recognition (OpenAI Whisper & Sarvam AI), LangChain LCEL orchestration, Mistral AI reasoning, and ChromaDB Retrieval-Augmented Generation (RAG) wrapped in a custom glassmorphism Streamlit UI.

---

## 📌 Overview & Resume Highlights

Designed for enterprise meeting intelligence, lecture analytics, and video knowledge extraction:
- **Zero Cloud Transcription Cost**: Runs local OpenAI Whisper directly on CPU/GPU without cloud API per-minute billing.
- **Multilingual Support**: Supports English via Whisper, and Hindi / Hinglish via Sarvam AI (`saaras:v2.5`) with automatic translation to English.
- **Privacy & Security**: Media files and vector embeddings remain on the local machine (`dowonolades/` & `vector_db/`), ideal for confidential business meetings.
- **End-to-End RAG Architecture**: Indexes transcribed speech chunks into persistent ChromaDB collections using HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`) and answers user queries strictly grounded in the meeting transcript.
- **Automated Intelligence Matrix**: Automatically extracts:
  - Concise Meeting Titles
  - Structured Executive Summaries
  - Action Items & Deliverables
  - Strategic Decisions Made
  - Unresolved Follow-up Questions

---

## 🛠️ Architecture & Tech Stack

| Layer | Component | Description |
|---|---|---|
| **Audio Acquisition** | `yt-dlp` & `pydub` | Ingests YouTube URLs or local video/audio files (`.mp4`, `.mp3`, `.wav`, `.m4a`), converts to standard 16kHz mono WAV, and slices into 10-minute processing chunks. |
| **Speech-to-Text (STT)** | OpenAI Whisper (Local) | High-accuracy local speech-to-text model for English audio. |
| **Indic STT** | Sarvam AI (`saaras`) | Specialised speech-to-text and translation for Hindi and Hinglish audio. |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` | Dense semantic vector representations running locally on CPU. |
| **Vector Store** | ChromaDB | Persistent local vector store for fast semantic similarity retrieval. |
| **LLM Orchestration** | LangChain (LCEL) + Mistral AI | `open-mistral-nemo` used for map-reduce summarization, key information extraction, and RAG Q&A. |
| **User Interface** | Streamlit | Glassmorphism dashboard with real-time pipeline status trackers, tabs, and interactive meeting chat. |

---

## 📁 Repository Structure

```
AI Video Assistant/
├── app.py                   # Streamlit Web Application (Glassmorphic UI & Interactive Chat)
├── main.py                  # CLI Pipeline Orchestrator (Terminal execution)
├── test.py                  # Pipeline verification and audio tests
├── project_des.txt          # Technical architecture & project design specification
├── req.txt                  # Python dependencies
├── requirements.txt         # Standard requirements alias
├── .env.example             # Template for API keys and configuration
├── core/
│   ├── transcribers.py      # OpenAI Whisper (Local) & Sarvam AI STT integration
│   ├── summarize.py         # Mistral AI LCEL meeting summarizer & title generator
│   ├── extractor.py         # Action items, key decisions, and questions extraction chains
│   ├── vector_store.py      # ChromaDB vector store builder, persistence & retriever
│   └── rag_engine.py        # Conversational LCEL RAG chain for question answering
├── utils/
│   └── audio_process.py     # YouTube audio download (yt-dlp), format standardization & chunking
└── dowonolades/             # Local cache for audio files and processing chunks
```

---

## 🚀 Getting Started (Local Setup)

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** (installed locally or automatically handled via `imageio-ffmpeg`)

### 2. Clone and Setup Environment
```bash
git clone https://github.com/Dhruvpratap2006/AI-Video-Assistant.git
cd "AI Video Assistant"

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r req.txt
```

### 3. Configure Environment Variables
Copy the template to `.env`:
```bash
cp .env.example .env
```
Add your credentials:
```env
MISTRAL_API_KEY=your_mistral_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_MODEL=saaras:v2.5
WHISPER_MODEL=small
```

> **API Key Resources:**
> - [Mistral AI Console](https://console.mistral.ai/)
> - [Sarvam AI Dashboard](https://dashboard.sarvam.ai/)

### 4. Run the Application

#### Option A: Streamlit UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. Enter any YouTube link or local media path and click **Analyse Video**.

#### Option B: Terminal CLI
```bash
python main.py
```

---

## 💡 System Design Note (Local vs Cloud Free Tier)

This system is deliberately architected to run on local workstations rather than resource-constrained cloud free tiers (such as Streamlit Cloud or HuggingFace Spaces free tier):
1. **Model Weight Footprint**: Running local Whisper models and dense transformer embeddings requires reliable CPU memory/GPU access that exceeds typical 1GB free tier sandbox limits.
2. **Streaming Anti-Bot Restrictions**: Cloud hosting provider IP ranges (e.g. AWS, GCP) are routinely rate-limited or blocked by YouTube when extracting video streams via `yt-dlp`. Running locally uses the client's residential network, ensuring uninterrupted extraction.
3. **Data Sovereignty**: Video recordings of meetings frequently contain proprietary or sensitive discussion that should not be transmitted to shared cloud servers.
