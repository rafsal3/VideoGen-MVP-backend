import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    print(f"MoviePy import error: {e}")
    MOVIEPY_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_video(data_json: str) -> str:
    """
    Simple video generation function - fallback if MoviePy has issues
    """
    if not MOVIEPY_AVAILABLE:
        logger.warning("MoviePy not available, returning dummy video URL")
        video_id = str(uuid.uuid4())
        return f"/static/audio/dummy_video_{video_id}.mp4"
    
    try:
        # Parse the input data
        if isinstance(data_json, str):
            data = json.loads(data_json)
        else:
            data = data_json
        
        audio_segments = data.get('audio_segments', [])
        assets = data.get('assets', [])
        
        if not audio_segments:
            raise Exception("No audio segments provided")
        
        return generate_simple_video(audio_segments, assets)
        
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        # Return dummy URL on error
        video_id = str(uuid.uuid4())
        return f"/static/audio/error_video_{video_id}.mp4"

def generate_video_from_segments(audio_segments: List[Dict], assets: List[Dict]) -> str:
    """
    Generate video directly from audio segments and assets lists
    """
    if not MOVIEPY_AVAILABLE:
        logger.warning("MoviePy not available, returning dummy video URL")
        video_id = str(uuid.uuid4())
        return f"/static/audio/dummy_video_{video_id}.mp4"
    
    return generate_simple_video(audio_segments, assets)

def generate_simple_video(audio_segments: List[Dict], assets: List[Dict]) -> str:
    """
    Simple video generation with basic MoviePy functionality
    """
    video_id = str(uuid.uuid4())
    output_filename = f"video_{video_id}.mp4"
    output_dir = "output"
    output_path = os.path.join(output_dir, output_filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        video_clips = []
        
        logger.info(f"Processing {len(audio_segments)} audio segments")
        
        for i, audio_segment in enumerate(audio_segments):
            logger.info(f"Processing segment {i + 1}/{len(audio_segments)}")
            
            # Get audio file path
            audio_path = audio_segment.get('audio_file_path')
            if not audio_path or not os.path.exists(audio_path):
                logger.warning(f"Audio file not found: {audio_path}, skipping segment")
                continue
            
            # Load audio to get duration
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                
                # Find corresponding asset
                segment_assets = [asset for asset in assets if asset.get('order_id') == i + 1]
                
                if segment_assets:
                    # Use first asset for this segment
                    asset = segment_assets[0]
                    asset_path = asset.get('url', '').replace('/assets/', 'output/assets/')
                    
                    if os.path.exists(asset_path):
                        # Create image clip with audio duration
                        image_clip = ImageClip(asset_path, duration=duration)
                        
                        # Resize to standard video size (1920x1080)
                        image_clip = image_clip.resize(height=1080)
                        if image_clip.w > 1920:
                            image_clip = image_clip.resize(width=1920)
                        
                        # Center the image
                        image_clip = image_clip.set_position('center')
                        
                        # Add audio to image clip
                        video_clip = image_clip.set_audio(audio_clip)
                        video_clips.append(video_clip)
                    else:
                        logger.warning(f"Asset file not found: {asset_path}")
                        # Create a simple colored background instead
                        from moviepy.editor import ColorClip
                        color_clip = ColorClip(size=(1920, 1080), color=(64, 128, 255), duration=duration)
                        video_clip = color_clip.set_audio(audio_clip)
                        video_clips.append(video_clip)
                else:
                    logger.warning(f"No assets found for segment {i}")
                    # Create a simple colored background
                    from moviepy.editor import ColorClip
                    color_clip = ColorClip(size=(1920, 1080), color=(128, 128, 128), duration=duration)
                    video_clip = color_clip.set_audio(audio_clip)
                    video_clips.append(video_clip)
                    
            except Exception as e:
                logger.error(f"Error processing segment {i}: {e}")
                continue
        
        if not video_clips:
            raise Exception("No video clips were created successfully")
        
        # Concatenate all clips
        logger.info("Concatenating video clips...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Write the final video
        logger.info(f"Writing final video to: {output_path}")
        final_video.write_videofile(
            output_path,
            fps=24,  # Lower FPS for faster processing
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        logger.info(f"Video generation completed: {output_path}")
        return f"/static/audio/{output_filename}"
        
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        raise Exception(f"Video generation failed: {str(e)}")