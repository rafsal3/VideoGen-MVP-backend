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
from dotenv import load_dotenv

# Load .env variables (very important for FastAPI startup)
load_dotenv()

# Import service functions
from services.script import generate_script_json_string
from services.audio import generate_audio
from services.transcript import generate_transcript
from services.assets import generate_assets
from services.mixer import generate_video_from_segments

# Initialize FastAPI
app = FastAPI()

# Enable CORS (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders
app.mount("/static/audio", StaticFiles(directory="output"), name="audio")
app.mount("/assets", StaticFiles(directory="output/assets"), name="assets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Pydantic model for input
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
    request_id: Optional[str] = None

class AutopilotInput(NewsInput):
    pass

class MixerInput(BaseModel):
    audio_segments: List[dict]
    assets: List[dict]
    show_subtitles: Optional[bool] = True
    request_id: Optional[str] = None

# --- Utility functions ---
def split_script_into_sentences(script: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?]) +', script)
    return [s.strip() for s in sentences if s.strip()]

def parse_script_sentences(script_data: str) -> List[str]:
    try:
        parsed = json.loads(script_data)
        if isinstance(parsed, dict) and 'sentences' in parsed:
            return parsed['sentences']
        elif isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    return split_script_into_sentences(script_data)

# --- Endpoints ---
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
        sentences = parse_script_sentences(data.text)
        if not sentences:
            raise Exception("No sentences found in script")

        audio_results = []
        for i, sentence in enumerate(sentences):
            logging.info(f"[{request_id}] Generating audio for sentence {i+1}/{len(sentences)}")
            result = generate_audio(sentence, segment_index=i, request_id=request_id)
            if "error" in result:
                raise Exception(f"Audio failed for sentence {i+1}: {result['error']}")
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
        logging.info(f"[{request_id}] Raw input: {data.text[:200]}")

        audio_segments = json.loads(data.text)
        logging.info(f"[{request_id}] Parsed {len(audio_segments)} audio segments")

        if not isinstance(audio_segments, list):
            raise Exception("Expected a list of audio segments")

        if len(audio_segments) == 0:
            raise Exception("No audio segments provided")

        first_segment = audio_segments[0]
        logging.info(f"[{request_id}] First segment keys: {list(first_segment.keys())}")

        transcript_result = generate_transcript(audio_segments)

        if isinstance(transcript_result, dict) and 'transcripts' in transcript_result:
            return {
                "status": "done",
                "transcripts": transcript_result['transcripts'],
                "total_segments": transcript_result.get('total_segments', len(transcript_result['transcripts'])),
                "successful_transcripts": transcript_result.get('successful_transcripts', 0),
                "request_id": request_id
            }
        else:
            return {
                "status": "done",
                "transcripts": transcript_result,
                "total_segments": len(transcript_result) if isinstance(transcript_result, list) else 0,
                "request_id": request_id
            }

    except json.JSONDecodeError as e:
        logging.error(f"[{request_id}] JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        logging.error(f"[{request_id}] Transcript generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assets")
async def asset_endpoint(data: NewsInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating assets for: {data.text[:100]}")

    try:
        assets = generate_assets(data.text)
        logging.info(f"[{request_id}] Assets returned: {len(assets)}")
        if not assets:
            logging.warning(f"[{request_id}] No assets generated. Check Gemini/Unsplash response.")
        return {"status": "done", "assets": assets, "request_id": request_id}

    except Exception as e:
        logging.error(f"[{request_id}] Asset generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mix")
async def video_endpoint(data: MixerInput):
    request_id = data.request_id or str(uuid.uuid4())
    logging.info(f"[{request_id}] Generating final video with {len(data.audio_segments)} segments and {len(data.assets)} assets")

    try:
        # Generate video using the new function
        video_url = generate_video_from_segments(
            audio_segments=data.audio_segments,
            assets=data.assets
        )
        
        return {
            "status": "done", 
            "video_url": video_url, 
            "request_id": request_id,
            "segments_processed": len(data.audio_segments),
            "assets_used": len(data.assets)
        }
    except Exception as e:
        logging.error(f"[{request_id}] Video mixing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))