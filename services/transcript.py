def generate_transcript(audio_segments: list) -> list:
    """
    Accepts a list of audio file paths and returns transcripts for each segment.
    Returns a dict with 'transcripts' key containing the list of transcript results.
    """
    all_transcripts = []
    
    for i, segment in enumerate(audio_segments):
        audio_path = segment.get("audio_file_path")
        if not audio_path:
            all_transcripts.append({
                "segment_index": segment.get("segment_index", i),
                "sentence": segment.get("sentence", ""),
                "error": f"Missing audio path for segment {i}"
            })
            continue

        try:
            print(f"Processing transcript for segment {i}: {segment.get('sentence', '')[:50]}...")
            transcript_data = make_transcript(audio_path)
            all_transcripts.append({
                "segment_index": segment.get("segment_index", i),
                "sentence": segment.get("sentence", ""),
                "transcript_text": transcript_data.get("text", ""),
                "words": transcript_data.get("words", []),
                "confidence": transcript_data.get("confidence", None)  # If available
            })
        except Exception as e:
            print(f"Error transcribing segment {i}: {e}")
            all_transcripts.append({
                "segment_index": segment.get("segment_index", i),
                "sentence": segment.get("sentence", ""),
                "error": str(e)
            })
    
    return all_transcripts


# transcriptmaker.py
import assemblyai as aai
from dotenv import load_dotenv
import json
import os

def make_transcript(audio_file_path):
    print("Generating Transcript ...")
    # Load environment variables
    load_dotenv()

    # AssemblyAI API setup
    api_key = os.getenv('ASSEMBLY_AI_API_KEY')
    if not api_key:
        raise EnvironmentError("ASSEMBLY_AI_API_KEY not found in environment variables.")
    aai.settings.api_key = api_key

    # Check if audio file exists
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    # Initialize transcription
    transcriber = aai.Transcriber()

    # Transcription configuration setup
    config = aai.TranscriptionConfig(
        word_boost=None,  # Add keywords to boost recognition accuracy (optional)
        boost_param=None,
        speaker_labels=False,  # Enable if you want speaker identification
        punctuate=True,  # Add punctuation to the transcription
        format_text=True   # Format text for readability
    )

    try:
        # Perform transcription
        transcript = transcriber.transcribe(audio_file_path, config)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")

        # Collect transcription result
        transcription_result = {
            "text": transcript.text,
            "words": [
                {
                    "start": word.start,
                    "end": word.end,
                    "word": word.text
                }
                for word in transcript.words
            ],
        }

        # Save transcription result to a JSON file (optional, for backup)
        transcript_path = "output/transcript/transcript.json"
        os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
        with open(transcript_path, 'w') as json_file:
            json.dump(transcription_result, json_file, indent=4)
        print("Transcript saved ...")
        
        # Return the actual transcript data instead of file path
        return transcription_result

    except Exception as e:
        raise Exception(f"Error in transcription: {e}")