import os
import json
import datetime
import numpy as np
import soundfile as sf
from typing import List, Dict

class AudioStitcher:
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            # Set default storage inside backend/storage/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.storage_dir = os.path.join(base_dir, "storage")
        else:
            self.storage_dir = storage_dir
            
        self.audiobooks_dir = os.path.join(self.storage_dir, "audiobooks")
        self.sessions_dir = os.path.join(self.storage_dir, "sessions")
        
        os.makedirs(self.audiobooks_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    def get_session_dir(self, session_id: str) -> str:
        """Returns and creates a dedicated temp directory for a generation session."""
        path = os.path.join(self.sessions_dir, session_id)
        os.makedirs(path, exist_ok=True)
        return path
        
    def save_chunk(self, session_id: str, chunk_idx: int, audio: np.ndarray, sample_rate: int) -> str:
        """Saves an individual generated speech chunk as a standard WAV file."""
        session_path = self.get_session_dir(session_id)
        file_name = f"chunk_{chunk_idx:04d}.wav"
        file_path = os.path.join(session_path, file_name)
        
        sf.write(file_path, audio, sample_rate)
        return file_path
        
    def stitch_session(self, session_id: str, title: str, character_info: List[Dict]) -> Dict:
        """
        Concatenates all chunk WAV files in a session folder in numerical order,
        saves the final unified audiobook, writes its metadata JSON card,
        and cleans up the session folder.
        """
        session_path = self.get_session_dir(session_id)
        
        # Gather all wav files and sort them numerically
        files = [f for f in os.listdir(session_path) if f.startswith("chunk_") and f.endswith(".wav")]
        files.sort()
        
        if not files:
            raise FileNotFoundError(f"No generated audio chunks found in session {session_id}")
            
        # Load text chunks metadata for passage timings
        chunks_meta = []
        chunks_meta_path = os.path.join(session_path, "text_chunks.json")
        if os.path.exists(chunks_meta_path):
            try:
                with open(chunks_meta_path, "r", encoding="utf-8") as f:
                    chunks_meta = json.load(f)
            except Exception as e:
                print(f"Error loading text_chunks for timing mapping: {e}")

        all_waveforms = []
        passages = []
        target_sr = 24000  # Standard target sample rate (Kokoro native)
        total_samples = 0
        
        for idx, file_name in enumerate(files):
            file_path = os.path.join(session_path, file_name)
            data, sr = sf.read(file_path)
            if sr != target_sr:
                from scipy.signal import resample
                num_samples = int(len(data) * target_sr / sr)
                data = resample(data, num_samples)
            all_waveforms.append(data)
            
            # Map start and end times in seconds
            chunk_len = len(data)
            start_time = total_samples / target_sr
            end_time = (total_samples + chunk_len) / target_sr
            total_samples += chunk_len
            
            speaker = "Narrator"
            text = ""
            emotion = "neutral"
            if idx < len(chunks_meta):
                speaker = chunks_meta[idx].get("speaker", "Narrator")
                text = chunks_meta[idx].get("text", "")
                emotion = chunks_meta[idx].get("emotion", "neutral")
                
            passages.append({
                "speaker": speaker,
                "text": text,
                "emotion": emotion,
                "start": round(start_time, 3),
                "end": round(end_time, 3)
            })
            
        # Concatenate waveforms
        if all_waveforms:
            master_waveform = np.concatenate(all_waveforms)
        else:
            master_waveform = np.zeros(target_sr)
            
        # Define output audiobook filenames
        safe_title = "".join([c if c.isalnum() or c in (" ", "_", "-") else "" for c in title]).strip().replace(" ", "_")
        audiobook_id = f"{safe_title}_{session_id[:8]}"
        
        audio_filename = f"{audiobook_id}.wav"
        audio_filepath = os.path.join(self.audiobooks_dir, audio_filename)
        
        # Save merged audio
        sf.write(audio_filepath, master_waveform, target_sr)
        
        # Calculate duration in seconds
        duration = len(master_waveform) / target_sr
        
        # Save metadata sidecar card
        metadata = {
            "id": audiobook_id,
            "title": title,
            "filename": audio_filename,
            "duration": duration,
            "date": datetime.datetime.now().isoformat(),
            "characters": character_info,
            "chunks_count": len(files),
            "passages": passages
        }
        
        meta_filepath = os.path.join(self.audiobooks_dir, f"{audiobook_id}.json")
        with open(meta_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        # Note: We do NOT delete the session directory or chunks here
        # to allow the user to continue streaming individual chunks progressively 
        # in the Home tab player even after compilation completes.
        
        return metadata

    def list_audiobooks(self) -> List[Dict]:
        """Lists all compiled audiobooks in storage by reading their JSON cards."""
        audiobooks = []
        
        if not os.path.exists(self.audiobooks_dir):
            return []
            
        files = [f for f in os.listdir(self.audiobooks_dir) if f.endswith(".json")]
        
        for file_name in files:
            path = os.path.join(self.audiobooks_dir, file_name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    audiobooks.append(meta)
            except Exception as e:
                print(f"Error loading audiobook metadata from {file_name}: {e}")
                
        # Sort by creation date descending
        audiobooks.sort(key=lambda x: x.get("date", ""), reverse=True)
        return audiobooks
