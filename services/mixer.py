import uuid

def generate_video(script: str) -> str:
    video_id = str(uuid.uuid4())
    return f"https://dummy-videos.com/{video_id}.mp4"
