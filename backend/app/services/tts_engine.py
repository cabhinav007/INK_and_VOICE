"""
Ink & Voice — Hybrid TTS Engine
================================
Uses TWO speech engines for maximum voice diversity:

1. **Kokoro-82M (ONNX)** — For the Narrator voice only.
   Beautiful emotional inflections, natural "lag and swag".

2. **Piper VCTK Medium** — For ALL character dialogues.
   109 completely unique, distinct speakers (male, female, young, old).
   Each character gets a genuinely different voice.

Both engines apply dynamic pitch/speed resampling for emotions
(sad, joy, angry) so every line sounds alive.
"""

import os
import sys
import json
import struct
import subprocess
import zipfile
import requests
import numpy as np
import soundfile as sf
import threading
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Kokoro engine (narrator only)
# ---------------------------------------------------------------------------
from kokoro_onnx import Kokoro

# ---------------------------------------------------------------------------
from app.core.constants import (
    VCTK_SPEAKERS,
    ALL_KOKORO_VOICES,
    KOKORO_MODEL_URL,
    KOKORO_VOICES_URL,
    PIPER_BINARY_URL,
    VCTK_MODEL_URL,
    VCTK_CONFIG_URL,
)
from app.services.emotion_engine import EmotionEngine


class HybridTTSEngine:
    """
    Dual-engine TTS:
      • Kokoro-82M for narrator (emotional, natural, flowing)
      • Piper VCTK medium for characters (109 unique voices)
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.models_dir = os.path.join(base_dir, "core", "models")
        else:
            self.models_dir = models_dir

        self.piper_dir = os.path.join(self.models_dir, "piper")
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.piper_dir, exist_ok=True)

        # Kokoro paths
        self.kokoro_model = os.path.join(self.models_dir, "kokoro-v1.0.onnx")
        self.kokoro_voices = os.path.join(self.models_dir, "voices-v1.0.bin")
        self.kokoro: Optional[Kokoro] = None

        # Piper paths
        self.piper_exe = os.path.join(self.piper_dir, "piper", "piper.exe")
        self.vctk_model = os.path.join(self.piper_dir, "en_GB-vctk-medium.onnx")
        self.vctk_config = os.path.join(self.piper_dir, "en_GB-vctk-medium.onnx.json")

        # Cache the VCTK sample rate (read from config on first use)
        self._vctk_sample_rate: Optional[int] = None
        self._lock = threading.Lock()
        self._models_verified = False

    # ------------------------------------------------------------------
    # Downloading helpers
    # ------------------------------------------------------------------
    def _download_file(self, url: str, dest: str, label: str, progress_callback=None):
        """Streams a file from *url* to *dest* with optional progress."""
        if os.path.exists(dest):
            return
        print(f"  >> Downloading {label}...")
        if progress_callback:
            progress_callback(f"Downloading {label}…")

        resp = requests.get(url, stream=True, allow_redirects=True)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        tmp = dest + ".tmp"
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total and progress_callback and downloaded % (1 << 20) < 65536:
                        pct = int(downloaded / total * 100)
                        progress_callback(f"Downloading {label}: {pct}%")
        os.replace(tmp, dest)
        print(f"  [OK] {label} downloaded.")

    def download_all_models(self, progress_callback=None):
        """Ensures every required file is present locally."""
        if self._models_verified:
            return
        with self._lock:
            if self._models_verified:
                return
            # Kokoro
            self._download_file(KOKORO_MODEL_URL, self.kokoro_model, "Kokoro ONNX model (narrator)", progress_callback)
            self._download_file(KOKORO_VOICES_URL, self.kokoro_voices, "Kokoro voices pack", progress_callback)

            # Piper binary
            piper_zip = os.path.join(self.piper_dir, "piper_windows.zip")
            if not os.path.exists(self.piper_exe):
                self._download_file(PIPER_BINARY_URL, piper_zip, "Piper TTS engine (Windows)", progress_callback)
                print("  >> Extracting Piper binary...")
                with zipfile.ZipFile(piper_zip, "r") as zf:
                    zf.extractall(self.piper_dir)
                if os.path.exists(piper_zip):
                    os.remove(piper_zip)
                print("  [OK] Piper extracted.")

            # VCTK model + config
            self._download_file(VCTK_MODEL_URL, self.vctk_model, "VCTK multi-speaker model (109 voices)", progress_callback)
            self._download_file(VCTK_CONFIG_URL, self.vctk_config, "VCTK config", progress_callback)
            
            self._models_verified = True

    # ------------------------------------------------------------------
    # Kokoro (narrator) initialisation
    # ------------------------------------------------------------------
    def _init_kokoro(self):
        if self.kokoro is None:
            with self._lock:
                if self.kokoro is None:
                    import onnxruntime as ort
                    
                    # Set up optimized session options for maximum CPU speed
                    sess_options = ort.SessionOptions()
                    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                    sess_options.intra_op_num_threads = 4
                    sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                    
                    # Check available providers (enable CUDA if GPU is configured)
                    available_providers = ort.get_available_providers()
                    providers = []
                    if "CUDAExecutionProvider" in available_providers:
                        providers.append("CUDAExecutionProvider")
                    providers.append("CPUExecutionProvider")
                    
                    print(f"Initializing Kokoro session with providers: {providers}")
                    session = ort.InferenceSession(
                        self.kokoro_model,
                        sess_options=sess_options,
                        providers=providers
                    )
                    
                    self.kokoro = Kokoro.from_session(session, self.kokoro_voices)

    # ------------------------------------------------------------------
    # Audio resampling (pitch shifting without changing duration)
    # ------------------------------------------------------------------
    @staticmethod
    def _resample(audio: np.ndarray, factor: float) -> np.ndarray:
        """
        Shift pitch by *factor* using linear interpolation resampling.
          factor > 1 → pitch UP  (child)
          factor < 1 → pitch DOWN (senior)
        """
        if abs(factor - 1.0) < 0.01:
            return audio
        old_len = len(audio)
        new_len = int(old_len / factor)
        return np.interp(
            np.linspace(0, old_len - 1, new_len),
            np.arange(old_len),
            audio,
        )

    # ------------------------------------------------------------------
    # VCTK sample rate helper
    # ------------------------------------------------------------------
    def _get_vctk_sample_rate(self) -> int:
        if self._vctk_sample_rate is not None:
            return self._vctk_sample_rate
        try:
            with open(self.vctk_config, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self._vctk_sample_rate = cfg.get("audio", {}).get("sample_rate", 22050)
        except Exception:
            self._vctk_sample_rate = 22050
        return self._vctk_sample_rate

    # ------------------------------------------------------------------
    # Piper VCTK synthesis (characters)
    # ------------------------------------------------------------------
    def _generate_piper(self, text: str, speaker_id: int, length_scale: float = 1.0) -> Tuple[np.ndarray, int]:
        """
        Synthesise *text* with the VCTK model via the Piper binary.
        Returns (float32_samples, sample_rate).
        """
        tmp_wav = os.path.join(self.models_dir, f"_piper_tmp_{os.getpid()}.wav")

        cmd = [
            self.piper_exe,
            "--model", self.vctk_model,
            "--output_file", tmp_wav,
            "--speaker", str(speaker_id),
            "--length-scale", str(length_scale),
        ]

        try:
            proc = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                print(f"Piper stderr: {proc.stderr[:300]}")
        except Exception as e:
            print(f"Piper execution error: {e}")

        # Read generated WAV
        if os.path.exists(tmp_wav):
            try:
                data, sr = sf.read(tmp_wav, dtype="float32")
                return data, sr
            finally:
                try:
                    os.remove(tmp_wav)
                except OSError:
                    pass

        # Fallback silence
        sr = self._get_vctk_sample_rate()
        return np.zeros(sr, dtype=np.float32), sr

    def _map_vctk_to_kokoro(self, vctk_id: str, gender: str, age_group: str) -> str:
        """
        Maps numeric VCTK speaker IDs to a diverse set of Kokoro voices to maintain
        compatibility with legacy configs or non-reloaded browser states.
        """
        if gender == "Female":
            if age_group == "Young":
                return "bf_emma"
            elif age_group == "Senior":
                return "bf_isabella"
            else:
                mapping = {
                    "1": "af_sarah",
                    "3": "af_bella",
                    "6": "af_sky",
                    "9": "af_heart",
                    "15": "af_alloy",
                    "20": "af_river"
                }
                return mapping.get(vctk_id, "af_nicole")
        else:
            if age_group == "Young":
                return "am_puck"
            elif age_group == "Senior":
                return "bm_george"
            else:
                mapping = {
                    "41": "am_adam",
                    "43": "am_michael",
                    "45": "bm_george",
                    "48": "bm_daniel",
                    "52": "am_fenrir",
                    "58": "bm_fable"
                }
                return mapping.get(vctk_id, "am_adam")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_speech(
        self,
        text: str,
        voice: str,
        gender: str,
        age_group: str,
        emotion: str,
        is_narrator: bool = False,
    ) -> Tuple[np.ndarray, int]:
        """
        Generate speech for a single text segment.
        All voice generation (narrator + characters) is routed through the Kokoro engine
        for beautiful, lifelike, expressive quality, and runs entirely in memory (no subprocesses).
        """
        self.download_all_models()
        self._init_kokoro()
        
        target_speed, pitch_factor = EmotionEngine.get_emotion_params(emotion, age_group, gender)
        
        # Standardize voice string: if it's a numeric VCTK ID (like "3"), map it to a Kokoro voice
        if voice.isdigit() or voice not in ALL_KOKORO_VOICES:
            voice = self._map_vctk_to_kokoro(voice, gender, age_group)
            
        kokoro_speed = target_speed / pitch_factor
        kokoro_speed = max(0.5, min(2.0, kokoro_speed))
        
        # Apply text-based emotional styling for neural expressive enhancement
        styled_text = EmotionEngine.apply_neural_styling(text, emotion)
            
        try:
            samples, sr = self.kokoro.create(
                text=styled_text, voice=voice, speed=kokoro_speed, lang="en-us"
            )
        except Exception as e:
            print(f"Kokoro error: {e}")
            samples = np.zeros(24000, dtype=np.float32)
            sr = 24000
            
        # Apply pitch shift via resampling
        samples = self._resample(samples, pitch_factor)
        return samples, sr


# Convenience alias used by main.py
TTSEngine = HybridTTSEngine
