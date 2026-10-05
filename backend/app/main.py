import os
import uuid
import json
import shutil
import numpy as np

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.services.novel_parser import NovelParser
from app.services.tts_engine import TTSEngine, VCTK_SPEAKERS
from app.services.stitcher import AudioStitcher

app = FastAPI(title="Ink & Voice API", version="1.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services Init
tts_engine = TTSEngine()
stitcher = AudioStitcher()

# Memory database for running statuses (persisted to files as well)
generation_statuses = {}

# Expose uploaded documents temp storage
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Clean up storage directories on startup to ensure temp file behavior
@app.on_event("startup")
async def startup_event():
    print("Clearing temporary and session audiobooks storage...")
    for folder in [stitcher.audiobooks_dir, stitcher.sessions_dir, TEMP_DIR]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")


@app.post("/api/upload")
async def upload_novel(file: UploadFile = File(...)):
    """Receives a novel file, parses it, caches text chunks, and returns detected characters."""
    file_id = uuid.uuid4().hex
    _, ext = os.path.splitext(file.filename.lower())
    
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .pdf, .docx, or .txt file.")
        
    temp_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # Parse novel
        text = NovelParser.extract_text(temp_path)
        chunks, characters = NovelParser.parse_novel(text)
        
        # Create session directory and cache chunks
        session_id = uuid.uuid4().hex
        session_path = stitcher.get_session_dir(session_id)
        
        # Cache chunks and characters in session directory to keep memory light
        with open(os.path.join(session_path, "text_chunks.json"), "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=4)
            
        with open(os.path.join(session_path, "characters.json"), "w", encoding="utf-8") as f:
            json.dump(characters, f, indent=4)
            
        # Write initial status
        status = {
            "session_id": session_id,
            "title": file.filename,
            "status": "pending",  # pending, generating, completed, error
            "progress": 0,
            "completed_chunks": [],
            "total_chunks": len(chunks),
            "audiobook_id": None
        }
        with open(os.path.join(session_path, "status.json"), "w", encoding="utf-8") as f:
            json.dump(status, f, indent=4)
            
        return {
            "session_id": session_id,
            "title": file.filename,
            "characters": characters,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing document: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/voices")
async def get_voice_catalog():
    """Returns the full Kokoro voice catalog grouped by gender and age."""
    return VCTK_SPEAKERS

@app.get("/api/preview")
async def get_voice_preview(voice: str, gender: str, ageGroup: str, emotion: str = "neutral"):
    """Generates a short voice preview using Kokoro and returns it directly."""
    text = "Hello! This is how I sound in Ink and Voice."
    if ageGroup == "Young":
        text = "Hi! This is how I sound in Ink and Voice!"
    elif ageGroup == "Senior":
        text = "Greetings. This is how I sound in Ink and Voice."
        
    try:
        samples, sr = tts_engine.generate_speech(
            text=text,
            voice=voice,
            gender=gender,
            age_group=ageGroup,
            emotion=emotion,
            is_narrator=True
        )
        
        import io
        import soundfile as sf
        from fastapi import Response
        
        out = io.BytesIO()
        sf.write(out, samples, sr, format="WAV")
        return Response(content=out.getvalue(), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

def background_generate_audiobook(session_id: str, voices_config: dict, title: str):
    """Deep background thread executing progressive TTS generation in parallel."""
    import threading
    import concurrent.futures
    import time

    start_time = time.time()
    session_path = stitcher.get_session_dir(session_id)
    status_file = os.path.join(session_path, "status.json")
    status_lock = threading.Lock()
    
    try:
        # Load text chunks
        with open(os.path.join(session_path, "text_chunks.json"), "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        # Initialize status as generating
        status = {
            "session_id": session_id,
            "title": title,
            "status": "generating",
            "progress": 0,
            "completed_chunks": [],
            "total_chunks": len(chunks),
            "audiobook_id": None,
            "generation_time": None
        }
        
        # Save initial status
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=4)
            
        generation_statuses[session_id] = status
        
        # Worker function for parallel voice generation
        def generate_single_chunk(idx: int, chunk: dict):
            speaker = chunk["speaker"]
            text = chunk["text"]
            emotion = chunk["emotion"]
            
            is_narrator = (speaker == "Narrator")
            speaker_config = voices_config.get(speaker, voices_config.get("Narrator", {
                "voice": "af_nicole" if is_narrator else "1",
                "gender": "Female",
                "ageGroup": "Mid-Age"
            }))
            
            voice = speaker_config["voice"]
            gender = speaker_config["gender"]
            age_group = speaker_config["ageGroup"]
            
            # Generate speech audio wave
            samples, sample_rate = tts_engine.generate_speech(
                text=text,
                voice=voice,
                gender=gender,
                age_group=age_group,
                emotion=emotion,
                is_narrator=is_narrator
            )
            
            # Special starting indicators on chunk 0 (Intro voice note)
            if idx == 0:
                try:
                    intro_text = f"Ink and Voice presents: {title}."
                    intro_samples, intro_sr = tts_engine.generate_speech(
                        text=intro_text,
                        voice="af_nicole",
                        gender="Female",
                        age_group="Mid-Age",
                        emotion="joy",
                        is_narrator=True
                    )
                    
                    silence_warmup = np.zeros(int(intro_sr * 1.5), dtype=np.float32)
                    silence_post = np.zeros(int(intro_sr * 0.8), dtype=np.float32)
                    
                    samples = np.concatenate([silence_warmup, intro_samples.astype(np.float32), silence_post, samples.astype(np.float32)])
                except Exception as ex:
                    print(f"Error generating intro cue: {ex}")
                    
            # Add trailing silence on the last chunk to end smoothly
            if idx == len(chunks) - 1:
                try:
                    silence_end = np.zeros(int(sample_rate * 1.5), dtype=np.float32)
                    samples = np.concatenate([samples.astype(np.float32), silence_end])
                except Exception as ex:
                    print(f"Error generating outro cue: {ex}")
            
            # Save chunk
            stitcher.save_chunk(session_id, idx, samples, sample_rate)
            
            # Update progress thread-safely
            with status_lock:
                status["completed_chunks"].append(idx)
                status["completed_chunks"].sort()
                status["progress"] = int((len(status["completed_chunks"]) / len(chunks)) * 100)
                
                # Periodically write progress card
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(status, f, indent=4)
                generation_statuses[session_id] = status

        # Run parallel workers using ThreadPoolExecutor (max 3 concurrent jobs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(generate_single_chunk, idx, chunk)
                for idx, chunk in enumerate(chunks)
            ]
            concurrent.futures.wait(futures)
            
        # Stitch all chunks together
        character_list = []
        for name, config in voices_config.items():
            character_list.append({
                "name": name,
                "gender": config["gender"],
                "ageGroup": config["ageGroup"],
                "voice": config["voice"]
            })
            
        meta = stitcher.stitch_session(session_id, title, character_list)
        
        # Calculate total generation + stitching duration
        generation_time = round(time.time() - start_time, 1)
        meta["generation_time"] = generation_time
        
        # Re-save metadata card with generation_time
        meta_filepath = os.path.join(stitcher.audiobooks_dir, f"{meta['id']}.json")
        try:
            with open(meta_filepath, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4)
        except Exception:
            pass
        
        # Complete status
        status["status"] = "completed"
        status["progress"] = 100
        status["audiobook_id"] = meta["id"]
        status["generation_time"] = generation_time
        
        # Save complete status (in audiobooks catalog now)
        meta_status_path = os.path.join(stitcher.audiobooks_dir, f"{meta['id']}_status.json")
        with open(meta_status_path, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=4)
            
        generation_statuses[session_id] = status
        
    except Exception as e:
        print(f"Generation worker failed for session {session_id}: {e}")
        try:
            status = {
                "session_id": session_id,
                "title": title,
                "status": "error",
                "progress": 0,
                "error_message": str(e),
                "completed_chunks": [],
                "total_chunks": 0,
                "audiobook_id": None
            }
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=4)
            generation_statuses[session_id] = status
        except Exception:
            pass

@app.post("/api/generate")
async def start_generation(payload: dict, background_tasks: BackgroundTasks):
    """Initiates progressive background TTS synthesis."""
    session_id = payload.get("session_id")
    voices_config = payload.get("voices")  # Dict of speaker -> voice mapping
    title = payload.get("title", "Audiobook")
    
    if not session_id or not voices_config:
        raise HTTPException(status_code=400, detail="Missing session_id or voices config.")
        
    session_path = os.path.join(stitcher.sessions_dir, session_id)
    if not os.path.exists(session_path):
        raise HTTPException(status_code=404, detail="Session not found or expired.")
        
    # Start generation thread
    background_tasks.add_task(
        background_generate_audiobook, 
        session_id=session_id, 
        voices_config=voices_config, 
        title=title
    )
    
    return {"message": "Audiobook generation started successfully.", "session_id": session_id}

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Returns active progress stats, allowing robust client side polling."""
    # Check memory first
    if session_id in generation_statuses:
        return generation_statuses[session_id]
        
    # Check session directory status.json
    session_path = os.path.join(stitcher.sessions_dir, session_id)
    status_file = os.path.join(session_path, "status.json")
    
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
                generation_statuses[session_id] = status
                return status
        except Exception:
            pass
            
    # Check finished status.json inside audiobooks folder
    if os.path.exists(stitcher.audiobooks_dir):
        files = [f for f in os.listdir(stitcher.audiobooks_dir) if f.endswith("_status.json")]
        for file_name in files:
            path = os.path.join(stitcher.audiobooks_dir, file_name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    status = json.load(f)
                    if status.get("session_id") == session_id:
                        generation_statuses[session_id] = status
                        return status
            except Exception:
                pass
                
    raise HTTPException(status_code=404, detail="Session or status card not found.")

@app.get("/api/audio/chunk/{session_id}/{chunk_idx}")
async def stream_audio_chunk(session_id: str, chunk_idx: int):
    """Streams a single processed paragraph WAV chunk, enabling progressive client playback."""
    session_path = os.path.join(stitcher.sessions_dir, session_id)
    file_name = f"chunk_{chunk_idx:04d}.wav"
    file_path = os.path.join(session_path, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio chunk not generated yet.")
        
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/api/audiobooks")
async def list_completed_audiobooks():
    """Lists all successfully compiled audiobooks from library catalogs."""
    return stitcher.list_audiobooks()

@app.get("/api/audio/file/{audiobook_id}")
async def stream_full_audiobook(audiobook_id: str):
    """Streams the completed master merged audiobook file for listening or downloading."""
    file_path = os.path.join(stitcher.audiobooks_dir, f"{audiobook_id}.wav")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audiobook file not found.")
        
    return FileResponse(file_path, media_type="audio/wav", filename=f"{audiobook_id}.wav")

@app.delete("/api/audiobooks/{audiobook_id}")
async def delete_audiobook(audiobook_id: str):
    """Deletes an audiobook WAV and its meta JSON from library catalog."""
    audio_path = os.path.join(stitcher.audiobooks_dir, f"{audiobook_id}.wav")
    meta_path = os.path.join(stitcher.audiobooks_dir, f"{audiobook_id}.json")
    status_path = os.path.join(stitcher.audiobooks_dir, f"{audiobook_id}_status.json")
    
    deleted = False
    for path in [audio_path, meta_path, status_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted = True
            except OSError:
                pass
                
    if deleted:
        return {"message": "Audiobook successfully deleted."}
    else:
        raise HTTPException(status_code=404, detail="Audiobook record not found.")

# Try to serve frontend build files if they exist (for production packaging)
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="frontend")
