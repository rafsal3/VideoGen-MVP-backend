from services.audiomakereleven import make_audio
import uuid
import os

def generate_audio(script_chunk: str) -> dict:
    audio_path = make_audio(script_chunk)  # generates and saves the file

    if not audio_path or not os.path.exists(audio_path):
        return {
            "error": "Failed to generate audio."
        }

    audio_filename = os.path.basename(audio_path)
    audio_url = f"/static/audio/{audio_filename}"

    return {
        "audio_url": audio_url,
        "transcript": {
            "text": script_chunk,
            "start": 0,
            "end": 5
        }
    }
