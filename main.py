from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Union
import logging
import uuid
import re
import os

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
    audio_file_path: Optional[str] = None
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
        result = generate_audio(data.text)

        if "error" in result:
            raise Exception(result["error"])

        return {
            "status": "done",
            "audio_url": result["audio_url"],
            "audio_file_path_on_server": result["audio_file_path"],
            "request_id": request_id
        }
    except Exception as e:
        logging.error(f"[{request_id}] Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcript")
async def transcript_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating transcript...")
    try:
        # data.text should contain the audio file path from the previous step
        transcript_data = generate_transcript(data.text)
        return {
            "status": "done", 
            "transcript": transcript_data, 
            "request_id": request_id
        }
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

