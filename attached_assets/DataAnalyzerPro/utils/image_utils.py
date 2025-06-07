import os
from PIL import Image
import logging

# Try to import rembg, but handle it gracefully if it fails
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except (ImportError, RuntimeError, Exception) as e:
    logging.warning(f"Background removal functionality is not available: {str(e)}")
    REMBG_AVAILABLE = False
    # Define a placeholder for the remove function to avoid unbound errors
    def remove(image_data):
        raise RuntimeError("Background removal not available")

def convert_image(input_path, output_path, target_format):
    """
    Convert an image to a different format.
    
    Args:
        input_path (str): Path to input image file
        output_path (str): Path to save the converted image
        target_format (str): Target format (e.g., 'png', 'jpg')
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if saving as JPEG
            if target_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Save with specified format
            img.save(output_path, format=target_format.upper())
        
        return True
    
    except Exception as e:
        logging.error(f"Error converting image: {str(e)}")
        return False

def remove_background(input_path, output_path):
    """
    Remove the background from an image using rembg.
    
    Args:
        input_path (str): Path to input image file
        output_path (str): Path to save the processed image
    
    Returns:
        tuple: (success, message) - (True, "") if successful, (False, error_message) otherwise
    """
    # Check if rembg is available
    if not REMBG_AVAILABLE:
        return False, "Background removal functionality is not available in this environment."
    
    try:
        # Open input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # Process the image
        output_data = remove(input_data)
        
        # Save the processed image
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)
        
        return True, ""
    
    except Exception as e:
        error_msg = f"Error removing background: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def compress_image(input_path, output_path, quality=70):
    """
    Compress an image to reduce file size.
    
    Args:
        input_path (str): Path to input image file
        output_path (str): Path to save the compressed image
        quality (int): Compression quality (1-100, where 100 is highest quality)
    
    Returns:
        tuple: On success: (original_size_str, compressed_size_str, reduction_percent)
               On failure: (None, None, None)
    """
    try:
        # Get original file size
        original_size = os.path.getsize(input_path)
        
        with Image.open(input_path) as img:
            # Determine format
            img_format = img.format
            if not img_format:
                img_format = os.path.splitext(input_path)[1][1:].upper()
                if img_format.lower() == 'jpg':
                    img_format = 'JPEG'
            
            # Convert to RGB if saving as JPEG
            if img_format.upper() in ['JPEG', 'JPG'] and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Save with compression
            img.save(
                output_path,
                format=img_format,
                optimize=True,
                quality=quality
            )
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        
        # Calculate size reduction
        reduction = original_size - compressed_size
        reduction_percent = int((reduction / original_size) * 100) if original_size > 0 else 0
        
        # Format sizes for display
        original_size_str = format_file_size(original_size)
        compressed_size_str = format_file_size(compressed_size)
        
        return original_size_str, compressed_size_str, reduction_percent
    
    except Exception as e:
        logging.error(f"Error compressing image: {str(e)}")
        return None, None, None

def format_file_size(size_bytes):
    """Format file size in bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            break
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} {unit}"
