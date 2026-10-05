<div align="center">

# 🎙️ Ink & Voice
### *Transforming Written Novels into Expressive, Multi-Cast AI Audiobooks*

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-005FE6?style=for-the-badge&logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Overview

**Ink & Voice** is an intelligent, full-stack AI platform that converts raw novels (`.pdf`, `.docx`, `.txt`) into immersive, multi-cast audiobooks. 

Unlike traditional single-voice Text-to-Speech (TTS) applications that sound monotonous, **Ink & Voice** uses heuristic NLP parsing to extract distinct characters, predict their age and gender demographics, assign unique voice actors, detect emotional cues in dialogue, and synthesize expressive human-like speech locally in real-time.

---

## ✨ Key Features

- 🎭 **Multi-Cast Character Attribution**  
  Automatically identifies speaker names in dialogue quotes using adjacent speech verb tags, vocative address heuristics, and alternating turn memory.
  
- 🧬 **Demographic Voice Assignment**  
  Predicts character gender (Male/Female) and age group (Young, Mid-Age, Senior) using multi-cultural naming databases and suffix patterns, mapping them to 20 distinct voice profiles.

- ⚡ **Lightweight & High-Performance (Kokoro-82M ONNX)**  
  Powered by quantized Kokoro-82M (~92MB FP8/INT8 ONNX model). Runs entirely in-memory on consumer CPUs at lightweight memory footprints (~320MB peak RAM) without needing expensive dedicated GPUs.

- 😡 **Biological Emotion & Neural Pre-Processing**  
  Dynamically modulates voice pitch and speed while injecting punctuation markers (`...`, `!`, `?!`) to trigger dramatic sighs, forceful shouts, or sorrowful hesitations.

- 🎵 **Progressive Streaming & Interactive Subtitles**  
  Listen to completed passages immediately as background threads continue synthesizing the rest of the book. Enjoy time-synced subtitle cards displaying active character text and emotion tags.

- 🔒 **Thread-Safe Optimized Concurrency**  
  Engineered with double-checked locking mechanisms (`threading.Lock()`) and cached model verification to prevent CPU contention during parallel multi-worker generation.

---

## 🏗️ System Architecture

```mermaid
graph TD
    %% Client Layer
    subgraph Client ["Client Layer (Vite + React)"]
        UI[Interactive UI / Home & Library]
        Player[Reusable HTML5 Audio Player & Subtitle Sync]
    end

    %% Gateway Layer
    subgraph API ["API Gateway (FastAPI)"]
        UploadEP["POST /api/upload"]
        GenerateEP["POST /api/generate"]
        StatusEP["GET /api/status/:id"]
        AudioEP["GET /api/audio/chunk/:id/:idx"]
    end

    %% Engine Layer
    subgraph Engine ["Core Engine Layer"]
        Parser["Novel Parser (NLP Segmentation & Heuristics)"]
        EmotionEng["Emotion Engine (Pitch/Speed & Punctuation Styling)"]
        TTSEng["Hybrid TTS Engine (Kokoro-82M ONNX)"]
        Stitcher["Audio Stitcher (WAV Concat & Metadata Management)"]
    end

    %% Flow Connections
    UI -->|Upload Document| UploadEP
    UploadEP --> Parser
    Parser -->|Extract Chunks & Characters| UI
    
    UI -->|Start Generation| GenerateEP
    GenerateEP -->|ThreadPoolExecutor (3 Workers)| TTSEng
    TTSEng --> EmotionEng
    
    Player <-->|Poll Progress| StatusEP
    Player <-->|Stream WAV Chunks| AudioEP
    
    TTSEng --> Stitcher
```

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | Async API server with multi-threaded execution pool |
| **Frontend** | React 18, Vite, Vanilla CSS | Fast SPA with responsive glassmorphism UI |
| **TTS Engine** | Kokoro-82M (ONNX Runtime) | Low-latency 24kHz neural speech generator |
| **Audio Processing** | PySoundFile, NumPy | Resampling pitch factor adjustment & silence padding |
| **Document Processing** | PyPDF, python-docx | Text extraction across PDF, Word, and TXT files |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** `v3.10` or higher installed
- **Node.js:** `v18.0` or higher installed

---

### 1. Clone & Setup Backend

```bash
# Navigate to the project backend
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Launch Backend Server

```bash
python run.py
```
*The FastAPI backend will start at `http://127.0.0.1:8000`.*

---

### 3. Setup & Launch Frontend

Open a new terminal window:

```bash
# Navigate to the frontend directory
cd frontend

# Install node dependencies
npm install

# Start the Vite development server
npm run dev
```
*The React application will launch at `http://localhost:5173` (or served statically via FastAPI).*

---

## 📂 Project Structure

```
By_anigravity/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── constants.py       # Naming databases, suffix rules, voice catalog
│   │   │   └── models/            # Quantized ONNX model binaries & config
│   │   ├── services/
│   │   │   ├── emotion_engine.py  # Emotion detection, pitch/speed modulation
│   │   │   ├── novel_parser.py    # Document text extraction & speaker attribution
│   │   │   ├── stitcher.py        # Audio chunk merger & library metadata manager
│   │   │   └── tts_engine.py      # Thread-safe Kokoro-82M ONNX speech generator
│   │   └── main.py                # FastAPI endpoints & async background workers
│   ├── run.py                     # Uvicorn server bootstrapper
│   └── requirements.txt           # Python dependency manifest
├── frontend/
│   ├── src/
│   │   ├── components/            # Navigation, Navbar, Header
│   │   ├── pages/                 # Home (Studio Player) & History (Library)
│   │   ├── App.jsx                # Main Application router & layout
│   │   └── index.css              # Custom Vanilla CSS styling
│   ├── package.json               # Node packages configuration
│   └── vite.config.js             # Vite build pipeline setup
├── MODEL_ARCHITECTURE.md          # Technical deep-dive on AI models
├── SYSTEM_DEVELOPMENT_REPORT.md   # Comprehensive system development report
└── README.md                      # Project documentation
```

---

## 📡 API Reference Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/upload` | `POST` | Uploads PDF/DOCX/TXT file, parses chunks, and returns detected characters |
| `/api/generate` | `POST` | Initiates multi-threaded background speech synthesis for a session |
| `/api/status/{session_id}` | `GET` | Fetches real-time generation progress and completed chunk list |
| `/api/audio/chunk/{session_id}/{idx}` | `GET` | Streams individual processed passage WAV chunk for client buffering |
| `/api/audiobooks` | `GET` | Retrieves catalog of all compiled audiobooks in the library |
| `/api/audio/file/{id}` | `GET` | Streams full merged audiobook WAV for download or master playback |

---

## 📜 Documentation

For further technical details, explore:
- 📄 [MODEL_ARCHITECTURE.md](file:///d:/MSc_Project/By_anigravity/MODEL_ARCHITECTURE.md) — Detailed specifications of Kokoro-82M, demographic voice allocation, and resampling mathematics.
- 📊 [SYSTEM_DEVELOPMENT_REPORT.md](file:///d:/MSc_Project/By_anigravity/SYSTEM_DEVELOPMENT_REPORT.md) — Complete development lifecycle, concurrency benchmarks, and optimization challenges.

---

<div align="center">

Made with ❤️ for AI Audio Experience

</div>
