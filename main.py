from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Union
import logging
import uuid
import re

# Import your service functions
from services.script import generate_script
from services.audio import generate_audio
from services.transcript import generate_transcript
from services.assets import generate_assets
from services.mixer import generate_video

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (configure origins properly for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in prod e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static audio directory
app.mount("/static/audio", StaticFiles(directory="output"), name="audio")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pydantic input schema
class NewsInput(BaseModel):
    text: str
    duration: Optional[str] = None
    model: Optional[str] = None
    resolution: Optional[str] = None
    frame_rate: Optional[str] = None
    aspect_ratio: Optional[str] = None
    format: Optional[str] = None
    audio_model: Optional[str] = None
    script_type: Optional[str] = None
    script_model: Optional[str] = None
    asset_type: Optional[str] = None
    asset_source: Optional[str] = None
    request_id: Optional[str] = None  # Optional incoming ID from frontend

# For autopilot input, allowing nested data for video mixer
class AutopilotInput(NewsInput):
    # Here, you can extend if you want to accept more detailed payloads
    pass

# Utility function to split script into sentences better than naive split
def split_script_into_sentences(script: str) -> List[str]:
    # This regex splits on sentence-ending punctuation + space, keeping sentences clean
    sentences = re.split(r'(?<=[.!?]) +', script)
    return [s.strip() for s in sentences if s.strip()]

@app.post("/script")
async def script_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating script...")
    try:
        script = generate_script(data.text)
        return {"status": "done", "script": script, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Script generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audio")
async def audio_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating audio...")
    try:
        audio = generate_audio(data.text)
        return {"status": "done", "audio": audio, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcript")
async def transcript_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating transcript...")
    try:
        transcript = generate_transcript(data.text)
        return {"status": "done", "transcript": transcript, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Transcript generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets")
async def asset_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating assets...")
    try:
        assets = generate_assets(data.text)
        return {"status": "done", "assets": assets, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Asset generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mix")
async def video_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating final video...")
    try:
        video_url = generate_video(data.text)
        return {"status": "done", "video_url": video_url, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Video mixing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/autopilot")
async def autopilot_endpoint(data: AutopilotInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Starting autopilot video generation...")

    try:
        # Generate full script
        script = generate_script(data.text)

        # Split script into sentences
        script_chunks = split_script_into_sentences(script)

        audio_outputs = []
        transcripts = []

        for chunk in script_chunks:
            if not chunk:
                continue
            audio = generate_audio(chunk)
            audio_outputs.append(audio)
            # If your audio generation returns a transcript field, collect it
            if isinstance(audio, dict) and 'transcript' in audio:
                transcripts.append(audio['transcript'])

        assets = generate_assets(data.text)

        # Prepare a payload dictionary for video mixer if it expects dict input
        video_input = {
            "script": script,
            "audio": audio_outputs,
            "transcript": transcripts,
            "assets": assets
        }

        video_url = generate_video(video_input)

        return {
            "status": "done",
            "job_id": request_id,
            "request_id": request_id,
            "script": script,
            "audio": audio_outputs,
            "transcript": transcripts,
            "assets": assets,
            "video_url": video_url
        }

    except Exception as e:
        logging.error(f"[{request_id}] Autopilot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
