from services.audiomakereleven import make_audio
import uuid
import os

def generate_audio(script_chunk: str, segment_index: int = 0, request_id: str = None) -> dict:
    """
    Generate audio for a single script chunk/sentence
    
    Args:
        script_chunk: The text to convert to audio
        segment_index: Index of the segment (for unique filename)
        request_id: Request ID for tracking
    
    Returns:
        Dictionary with audio_url and audio_file_path or error
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Create unique filename for this segment
    audio_path = make_audio(script_chunk, segment_index=segment_index, request_id=request_id)

    if not audio_path or not os.path.exists(audio_path):
        return {"error": f"Failed to generate audio for segment {segment_index}."}

    audio_filename = os.path.basename(audio_path)
    audio_url = f"/static/audio/{audio_filename}"

    return {
        "audio_url": audio_url,
        "audio_file_path": audio_path
    }