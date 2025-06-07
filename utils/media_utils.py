import os
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import wave
from utils.file_handler import format_file_size, get_file_size_str

def convert_audio_to_video(audio_path, output_path, background_color='#000000', background_image=None, width=640, height=480):
    """
    Convert an audio file to a video file with a static background.
    
    Args:
        audio_path (str): Path to the input audio file
        output_path (str): Path to save the output video file
        background_color (str): Hex color code for background if no image is provided
        background_image (str): Path to an image to use as background (optional)
        width (int): Width of the output video
        height (int): Height of the output video
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Create a folder to store temporary frame images
        temp_dir = os.path.dirname(output_path)
        frames_dir = os.path.join(temp_dir, 'frames')
        os.makedirs(frames_dir, exist_ok=True)
        
        # Create a static background image
        frame = None
        if background_image and os.path.exists(background_image):
            try:
                # Use the provided background image
                frame = Image.open(background_image)
                frame = frame.resize((width, height))
            except Exception as e:
                # If loading the image fails, fall back to a colored background
                print(f"Error loading background image: {e}")
                frame = None
        
        if frame is None:
            # Create a solid color background
            frame = Image.new('RGB', (width, height), background_color)
            
            # Add a simple audio visualization graphic
            draw = ImageDraw.Draw(frame)
            draw.text((width//2, height//2), "Audio Visualization", fill="white", anchor="mm")
            
        # Save the frame
        frame_path = os.path.join(frames_dir, 'background.png')
        frame.save(frame_path)
        
        # Generate the video with ffmpeg
        # Use ffmpeg to convert audio to video with the static image
        ffmpeg_cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', frame_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ]
        
        process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            return False, f"FFmpeg error: {process.stderr}"
        
        # Get file sizes for reporting
        input_size = format_file_size(os.path.getsize(audio_path))
        output_size = format_file_size(os.path.getsize(output_path))
        
        return True, f"Conversion successful. Input size: {input_size}, Output size: {output_size}"
    
    except Exception as e:
        return False, str(e)