from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os

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

def make_audio(script):
    print("Generating Audio...")

    # Voice ID and model ID for ElevenLabs
    voice_id = "qwaVDEGNsBllYcZO1ZOJ"  # Replace with your desired voice ID
    model_id = "eleven_multilingual_v2"  # Replace with your desired model ID

    # Output folder
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist

    # File path for the audio output
    file_path = os.path.join(output_dir, "audio.mp3")

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

        print(f"Audio generated and saved as {file_path}")
        return file_path  # Return the file path of the saved audio file

    except Exception as e:
        print(f"Error: {e}")
        return None
