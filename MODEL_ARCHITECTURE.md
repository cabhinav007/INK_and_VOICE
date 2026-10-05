# Ink & Voice — AI Model Architecture Guide

This document outlines the models, engines, and design choices used in the **Ink & Voice** platform. Use this guide to structure your presentation and explain the technical architecture of the system.

---

## 1. Core Synthesis Model: Kokoro-82M (ONNX quantized)

### Purpose
* Generates the high-fidelity audio for both the **Narrator** and **all characters**.
* Synthesizes emotional, human-like voice inflections from parsed text.

### Technical Specifications
* **Parameters:** 82 Million (highly optimized).
* **Size:** ~92MB (FP8/INT8 quantized ONNX format).
* **Output Sample Rate:** 24,000 Hz (24kHz).
* **Runtime Engine:** `onnxruntime` (C++ backend with Python bindings).

### Why We Use It
1. **Unmatched Efficiency-to-Quality Ratio:** At only 92MB, it runs comfortably on consumer-grade CPUs with minimal RAM, yet produces studio-quality, natural human speech that outperforms traditional models 10x its size (such as Bark or tortoise-tts, which require heavy GPUs and gigabytes of storage).
2. **Organic Flow (Lag & Swag):** Kokoro incorporates a state-of-the-art duration predictor that gives speech natural micro-pauses, realistic breathing rhythms, and conversational cadence instead of sounding robotic or monotone.
3. **Low-Latency Inference:** Because it is compiled into ONNX format, it executes in C++ speed. It processes standard paragraph sentences in **less than 200 milliseconds**, enabling progressive, real-time buffering.

---

## 2. Demographic voice Catalog & Speaker Heuristics

### Purpose
* Automatically assigns distinct, realistic voices to every character detected in the novel.
* Groups voices by **Gender** (Male/Female) and **Age Group** (Young, Mid-Age, Senior).

### Design Architecture
* The system defines a voice database of **20 distinct, high-quality Kokoro voices** (including regional accents like US Bright, US Soft, UK Conversational, UK Measured).
* When `novel_parser.py` scans the document, it extracts character names and estimates their demographics using suffix heuristics (e.g. names ending in `devi` or `ita` as Female, `esh` or `dev` as Male) and surrounding context (e.g., scoring words like "grandfather" or "elderly" for Senior, and "child" or "kid" for Young).
* Characters are then assigned index-cycled voices matching their exact demographic pool, guaranteeing that Vikram, Meera, the Narrator, and any senior characters sound completely unique.

---

## 3. Dynamic Emotion Engine & Neural Styling

### Purpose
* Enhances the expressiveness of dialogue lines by modifying pitch, tempo, and intonation based on emotional triggers (**Sad**, **Joy**, **Angry**, **Neutral**).

### Technical Execution

#### A. Biological Parameter Resampling (Pitch & Tempo)
We adjust the pitch and speed multipliers dynamically to simulate human emotional response:
* **Sad:** Pitch is lowered to **0.82x** and tempo is slowed to **0.70x** to simulate a solemn, heavy, and melancholic delivery.
* **Joy:** Pitch is elevated to **1.20x** and tempo is quickened to **1.20x** for a bright, energetic, and excited tone.
* **Angry:** Pitch is raised to **1.12x** and tempo is set to **1.20x** to create a tense, rapid-fire, and sharp vocal delivery.

*How it works under the hood:* The speed is adjusted natively in the Kokoro model, while the pitch shifting is achieved via **linear interpolation resampling** using NumPy (`numpy.interp`). This shifts the pitch up or down without causing robotic digital distortion.

#### B. Neural Punctuation Injection (Text Pre-Processing)
Modern neural TTS models are highly sensitive to punctuation. They change their vocal intonation, stress patterns, and energy levels depending on commas, periods, exclamation points, and ellipses.
The **Emotion Engine** pre-processes the text string before feeding it to the model:
* **Angry lines:** Automatically replaces ending punctuation with `!` or `?!` (e.g., changing *"Hello."* to *"Hello!"*), forcing the model to generate a sharper, high-energy, and aggressive delivery.
* **Sad lines:** Injects ellipses (`...`) between phrase boundaries (e.g., changing *"I didn't know, she was gone."* to *"I didn't know... she was gone..."*), forcing the neural network to synthesize realistic hesitations, pauses, and sigh-like intonations.

---

## 4. Multi-threaded Parallel processing (FastAPI Backend)

### Purpose
* Enables fast generation times by synthesizing multiple audiobook paragraphs concurrently.

### Design Architecture
* Uses a `ThreadPoolExecutor` with a pool of **3 parallel worker threads** to generate speech for chunks concurrently.
* **Thread-Safe Double-Checked Lock:** Optimized with a mutual exclusion lock (`threading.Lock()`) to ensure that only the first thread initializes the ONNX Inference session on startup, preventing CPU/RAM crashes from concurrent model loading.
* **Progressive Client Playback:** As each chunk WAV is generated, it is stored in the session directory. The frontend React player can stream completed chunks immediately using `/api/audio/chunk/...` while the rest of the book is still generating, avoiding any start-up wait for the user.
