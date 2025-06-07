import os
from flask import current_app

def allowed_file(filename, file_type):
    """
    Check if a file has an allowed extension for a specific file type.
    
    Args:
        filename (str): The name of the file to check
        file_type (str): The type of file ('pdf', 'image', 'document')
    
    Returns:
        bool: True if the file has an allowed extension, False otherwise
    """
    if not filename:
        return False
        
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {}).get(file_type, [])
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size_str(file_path):
    """
    Get a human-readable file size string.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: Human-readable file size (e.g., "2.5 MB")
    """
    size_bytes = os.path.getsize(file_path)
    return format_file_size(size_bytes)

def format_file_size(size_bytes):
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes (int): File size in bytes
    
    Returns:
        str: Human-readable file size (e.g., "2.5 MB")
    """
    # Convert to human-readable form
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            break
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} {unit}"

def clean_temp_files(directory, max_age_hours=24):
    """
    Clean temporary files that are older than a specified age.
    
    Args:
        directory (str): Directory containing temporary files
        max_age_hours (int): Maximum age of files in hours before deletion
    """
    import time
    from datetime import datetime, timedelta
    
    # Get current time
    now = datetime.now()
    max_age = timedelta(hours=max_age_hours)
    
    # Walk through directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Get file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # If file is older than max_age, delete it
            if now - file_time > max_age:
                try:
                    os.remove(file_path)
                except Exception as e:
                    # Log the error but continue
                    print(f"Error removing file {file_path}: {e}")
