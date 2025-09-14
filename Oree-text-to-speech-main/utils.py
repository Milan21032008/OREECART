import os
import logging
from PIL import Image, ImageDraw, ImageFont
import tempfile
import subprocess
from gtts import gTTS

def generate_audio(text, output_path, rate=200):
    """
    Generate audio from text using gTTS only (cloud compatible)
    """
    try:
        tts = gTTS(text)
        tts.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            raise Exception("gTTS failed to generate audio file")
    except Exception as e:
        logging.error(f"Error generating audio with gTTS: {str(e)}")
        return False

def generate_video(text, output_path, bg_color="#000000", text_color="#FFFFFF", duration=10):
    """
    Generate a simple video with text using PIL and FFmpeg
    Optimized for lower memory usage and faster processing
    """
    try:
        logging.info("Starting video generation")
        # Video dimensions reduced to 640x360 for optimization
        width, height = 640, 360
        fps = 15  # Reduced frame rate
        total_frames = duration * fps
        
        # Convert hex colors to RGB tuples
        bg_rgb = _hex_to_rgb(bg_color)
        text_rgb = _hex_to_rgb(text_color)
        
        # Calculate font size based on text length, smaller base font size
        base_font_size = 30
        if len(text) > 100:
            font_size = max(15, base_font_size - (len(text) // 20))
        else:
            font_size = base_font_size
        
        # Try to load a font
        font = _get_available_font(font_size)
        
        # Create temporary directory for frames
        with tempfile.TemporaryDirectory() as temp_dir:
            frame_pattern = os.path.join(temp_dir, "frame_%06d.png")
            
            # Generate frames
            for frame_num in range(total_frames):
                # Create image
                img = Image.new('RGB', (width, height), bg_rgb)
                draw = ImageDraw.Draw(img)
                
                # Wrap text if it's too wide
                wrapped_text = _wrap_text(text, font, width * 0.8, draw)
                
                # Calculate text dimensions for wrapped text
                bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Calculate position for centered text
                x_offset = (width - text_width) // 2
                y_offset = (height - text_height) // 2
                
                draw.multiline_text(
                    (x_offset, y_offset),
                    wrapped_text,
                    font=font,
                    fill=text_rgb,
                    align="center"
                )
                
                # Save frame
                frame_path = frame_pattern % frame_num
                img.save(frame_path)
            
            # Use FFmpeg to create video from frames with compression options
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '28',  # Higher CRF for more compression
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logging.info("Video generation completed successfully")
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            else:
                logging.error(f"FFmpeg error: {result.stderr}")
                return False
        
    except MemoryError:
        logging.error("MemoryError: Video generation ran out of memory")
        return False
    except Exception as e:
        logging.error(f"Error generating video: {str(e)}")
        return False

def _hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _get_available_font(size):
    """Get an available font with fallbacks"""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        '/System/Library/Fonts/Arial.ttf',
        '/Windows/Fonts/arial.ttf'
    ]
    
    # Try specific font files
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    
    # Fallback to default font
    try:
        return ImageFont.load_default()
    except Exception:
        # Ultimate fallback
        return ImageFont.load_default()

def _wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Word is too long, add it anyway
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def get_file_size_mb(file_path):
    """
    Get file size in MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except:
        return 0
