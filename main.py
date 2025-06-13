from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Union
import logging
import uuid
import re
import os
import json

# Import your service functions
from services.script import generate_script_json_string
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
app.mount("/assets", StaticFiles(directory="output/assets"), name="assets")

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

def parse_script_sentences(script_data: str) -> List[str]:
    """Extract sentences from script JSON or plain text"""
    try:
        # Try to parse as JSON first
        parsed = json.loads(script_data)
        if isinstance(parsed, dict) and 'sentences' in parsed:
            return parsed['sentences']
        elif isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # If not JSON, split by periods
    return split_script_into_sentences(script_data)

@app.post("/script")
async def script_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating script...")
    try:
        script = generate_script_json_string(data.text)
        return {"status": "done", "script": script, "request_id": request_id}
    except Exception as e:
        logging.error(f"[{request_id}] Script generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audio")
async def audio_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating audio...")
    try:
        # Parse the script to get individual sentences
        sentences = parse_script_sentences(data.text)
        
        if not sentences:
            raise Exception("No sentences found in script")
        
        # Generate audio for each sentence
        audio_results = []
        for i, sentence in enumerate(sentences):
            logging.info(f"[{request_id}] Generating audio for sentence {i+1}/{len(sentences)}")
            result = generate_audio(sentence, segment_index=i, request_id=request_id)
            
            if "error" in result:
                raise Exception(f"Failed to generate audio for sentence {i+1}: {result['error']}")
            
            audio_results.append({
                "segment_index": i,
                "sentence": sentence,
                "audio_url": result["audio_url"],
                "audio_file_path": result["audio_file_path"]
            })

        return {
            "status": "done",
            "audio_segments": audio_results,
            "total_segments": len(audio_results),
            "request_id": request_id
        }
    except Exception as e:
        logging.error(f"[{request_id}] Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcript")
async def transcript_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating segmented transcript...")

    try:
        logging.info(f"[{request_id}] Raw input: {data.text[:200]}")  # Show more of the input
        
        # Parse the audio segments from the JSON string
        audio_segments = json.loads(data.text)
        logging.info(f"[{request_id}] Parsed {len(audio_segments)} audio segments")

        if not isinstance(audio_segments, list):
            raise Exception("Expected a list of audio segments")

        if len(audio_segments) == 0:
            raise Exception("No audio segments provided")

        # Log the structure of the first segment for debugging
        if audio_segments:
            first_segment = audio_segments[0]
            logging.info(f"[{request_id}] First segment structure: {list(first_segment.keys())}")

        # Generate transcripts for all segments
        transcript_result = generate_transcript(audio_segments)
        
        # Handle both old and new return formats
        if isinstance(transcript_result, dict) and 'transcripts' in transcript_result:
            # New format - return as is
            return {
                "status": "done",
                "transcripts": transcript_result['transcripts'],
                "total_segments": transcript_result.get('total_segments', len(transcript_result['transcripts'])),
                "successful_transcripts": transcript_result.get('successful_transcripts', 0),
                "request_id": request_id
            }
        else:
            # Old format - wrap in transcripts key for consistency
            return {
                "status": "done",
                "transcripts": transcript_result,
                "total_segments": len(transcript_result) if isinstance(transcript_result, list) else 0,
                "request_id": request_id
            }

    except json.JSONDecodeError as e:
        logging.error(f"[{request_id}] JSON decode error: {e}")
        logging.error(f"[{request_id}] Raw data: {data.text}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
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