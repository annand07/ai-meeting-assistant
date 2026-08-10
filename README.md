# 🎬 AI Meeting Assistant

An end-to-end AI pipeline that transcribes, summarizes, and lets you **chat with** any meeting recording or YouTube video — built entirely in Python.

Paste a YouTube URL or upload an audio/video file, and get:
- 📝 A full transcript (with Hindi → English translation support)
- 🧠 An AI-generated summary, key decisions, and action items
- 💬 A chat interface to ask questions directly about the content (RAG-powered)
- 📄 Exportable results as PDF or TXT

---

## ✨ Features

- **Flexible input** — YouTube URL or local audio/video file upload
- **Local transcription** — runs OpenAI's Whisper model on-device (no data leaves your machine, no per-minute API cost)
- **Hindi → English translation** — built-in via Whisper's translate mode
- **AI summarization** — LangChain (LCEL) pipeline powered by the Mistral API extracts summaries, key decisions, and action items
- **Chat with your transcript** — Retrieval-Augmented Generation (RAG) using ChromaDB + Hugging Face embeddings
- **Export** — download results as PDF or TXT
- **Simple UI** — built with Streamlit, no frontend code required

---

## 🏗️ Architecture

```
User Input (YouTube URL or file)
        │
        ▼
  process_input() ── detects URL vs local file
        │
        ▼
 download_youtube_audio() [yt-dlp]  OR  local file
        │
        ▼
   convert_to_wav() [pydub] ── mono, 16kHz
        │
        ▼
     chunk_audio() ── splits into chunks
        │
        ▼
  transcribe_all() [Whisper] ── per-chunk transcription
        │
        ▼
      Combined transcript
        │
        ▼
 LangChain (LCEL) → Mistral API
 → Summary + Action Items + Key Decisions
        │
        ▼
 Transcript chunks → Hugging Face embeddings → ChromaDB
        │
        ▼
   Chat with transcript (RAG retrieval + Mistral generation)
        │
        ▼
        Streamlit UI
        │
        ▼
    Export as PDF / TXT
```

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| Audio download | `yt-dlp` |
| Audio conversion | `FFmpeg` + `pydub` |
| Transcription | `Whisper` (local) |
| Orchestration | `LangChain` (LCEL) |
| LLM | `Mistral API` |
| Vector store | `ChromaDB` |
| Embeddings | `Hugging Face` (sentence-transformers) |
| UI | `Streamlit` |
| Export | `fpdf2` / `reportlab` |

---

## 📁 Project Structure

```
Video Agent/
├── app.py                    # Streamlit UI
├── main.py                   # Entry point / pipeline runner
├── test.py                   # Test script
├── requirements.txt
├── core/
│   ├── transcriber.py        # Whisper transcription logic
│   ├── summarizer.py         # LangChain + Mistral summarization
│   ├── extractor.py          # Action items / key decisions extraction
│   ├── rag_engine.py         # RAG query pipeline
│   └── vector_store.py       # ChromaDB integration
└── utils/
    └── audio_processor.py    # Download, convert, and chunk audio
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or 3.11 recommended
- [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) installed and on your system PATH
- A free [Mistral API](https://mistral.ai/) key

### Installation

```bash
git clone https://github.com/annand07/ai-meeting-assistant.git
cd ai-meeting-assistant

python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Run the app

```bash
streamlit run app.py
```

---

## 🧠 How It Works

1. **Input** — a YouTube link or uploaded file is detected and routed accordingly.
2. **Audio extraction** — `yt-dlp` downloads the audio (if a URL), and `FFmpeg`/`pydub` standardize it to 16kHz mono WAV — the format Whisper expects.
3. **Chunking** — long audio is split into manageable chunks to avoid memory issues.
4. **Transcription** — each chunk is transcribed locally via Whisper. Hindi audio is translated to English using Whisper's built-in translate task.
5. **Summarization** — the full transcript is passed through a LangChain LCEL pipeline (`prompt | llm | parser`) to the Mistral API, producing a summary, key decisions, and action items.
6. **RAG chat** — the transcript is embedded (Hugging Face) and stored in ChromaDB. User questions are embedded and matched against stored chunks via similarity search, with relevant context passed to Mistral for grounded answers.
7. **Export** — final results can be downloaded as PDF or TXT.

---

## 🐛 Challenges & Learnings

- **YouTube 403 errors** — worked around anti-bot detection by configuring `yt-dlp`'s `extractor_args` to use the Android client.
- **Silent chunking bug** — a misplaced `return` inside a loop caused only the first audio chunk to ever be processed; fixed by correcting indentation.
- **Windows PATH quirks** — FFmpeg/Git installs required fresh terminal sessions before becoming available, a good reminder of how environment variables propagate per-session.
- **Dependency conflicts** — pinned `numba`/`llvmlite` versions to resolve a Python 3.12 build failure with Whisper's dependencies.

---

## 🔮 Future Improvements

- Speaker diarization (who said what)
- Real-time/live transcription support
- Better error handling for invalid URLs and API failures
- GPU-backed deployment for faster transcription
- LangGraph-based agent for automatic retry/validation of low-quality summaries

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
