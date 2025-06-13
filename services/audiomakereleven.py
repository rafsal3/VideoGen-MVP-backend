from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import uuid
from datetime import datetime

load_dotenv()

# Get API key from environment variables
api_key = os.getenv('ELEVENLABS_API_KEY')
if not api_key:
    raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

# Initialize ElevenLabs client with API key
client = ElevenLabs(api_key=api_key)

def read_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def make_audio(script, segment_index=0, request_id=None):
    """
    Generate audio for a script segment
    
    Args:
        script: Text to convert to audio
        segment_index: Index of the segment for unique naming
        request_id: Request ID for tracking
    
    Returns:
        File path of the generated audio or None if failed
    """
    print(f"Generating Audio for segment {segment_index}...")

    # Voice ID and model ID for ElevenLabs
    voice_id = "qwaVDEGNsBllYcZO1ZOJ"  # Replace with your desired voice ID
    model_id = "eleven_multilingual_v2"  # Replace with your desired model ID

    # Output folder
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist

    # Create unique filename for this segment
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_segment_{segment_index}_{request_id}_{timestamp}.mp3"
    file_path = os.path.join(output_dir, filename)

    try:
        # Generate audio using ElevenLabs API
        audio_stream = client.text_to_speech.convert(
            text=script,
            voice_id=voice_id,
            model_id=model_id,
            output_format="mp3_44100_128",
        )

        # Save the audio to a file by consuming the generator
        with open(file_path, "wb") as audio_file:
            # Iterate through the generator and write each chunk
            for chunk in audio_stream:
                audio_file.write(chunk)

        print(f"Audio segment {segment_index} generated and saved as {file_path}")
        return file_path  # Return the file path of the saved audio file

    except Exception as e:
        print(f"Error generating audio segment {segment_index}: {e}")
        return None