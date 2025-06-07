import os
from flask import Blueprint, render_template, request, redirect, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
import uuid
from utils.file_handler import allowed_file
from utils.media_utils import convert_audio_to_video
from flask_login import login_required, current_user
from models import db, FileOperation

media_tools = Blueprint('media_tools', __name__)

@media_tools.route('/audio-to-video')
def audio_to_video():
    """Render the audio to video converter page"""
    return render_template('media/audio_to_video.html')

@media_tools.route('/audio-to-video', methods=['POST'])
@login_required
def audio_to_video_process():
    """Process audio to video conversion"""
    if 'audio_file' not in request.files:
        flash('No audio file part', 'danger')
        return redirect(request.url)
    
    audio_file = request.files['audio_file']
    
    if audio_file.filename == '':
        flash('No selected audio file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(audio_file.filename, 'audio'):
        flash('File type not allowed. Please upload an audio file (MP3, WAV, etc.)', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save the audio file
    audio_filename = secure_filename(audio_file.filename)
    audio_path = os.path.join(upload_path, audio_filename)
    audio_file.save(audio_path)
    
    # Set output filename
    output_filename = request.form.get('output_filename', 'converted_video.mp4')
    if not output_filename.lower().endswith('.mp4'):
        output_filename += '.mp4'
        
    output_filename = secure_filename(output_filename)
    output_path = os.path.join(upload_path, output_filename)
    
    # Get background color or image if provided
    background_color = request.form.get('background_color', '#000000')
    background_image = None
    if 'background_image' in request.files:
        bg_file = request.files['background_image']
        if bg_file and bg_file.filename != '' and allowed_file(bg_file.filename, 'image'):
            bg_filename = secure_filename(bg_file.filename)
            bg_path = os.path.join(upload_path, bg_filename)
            bg_file.save(bg_path)
            background_image = bg_path
    
    try:
        # Convert audio to video
        success, message = convert_audio_to_video(
            audio_path, 
            output_path, 
            background_color=background_color,
            background_image=background_image
        )
        
        # Store operation in database
        if current_user.is_authenticated:
            operation = FileOperation(
                user_id=current_user.id,
                operation_type='audio_to_video',
                original_filename=audio_filename,
                result_filename=output_filename,
                input_path=audio_path,
                output_path=output_path,
                parameters=f"BG Color: {background_color}, BG Image: {'Yes' if background_image else 'No'}",
                status='completed' if success else 'failed',
                error_message='' if success else message
            )
            db.session.add(operation)
            db.session.commit()
        
        if success:
            flash('Audio converted to video successfully!', 'success')
            # Pass the result file path for download
            result_file = os.path.join(operation_id, output_filename)
            return render_template('media/audio_to_video.html', result_file=result_file)
        else:
            flash(f'Error converting audio to video: {message}', 'danger')
            return redirect(request.url)
            
    except Exception as e:
        flash(f'Error during conversion: {str(e)}', 'danger')
        return redirect(request.url)

@media_tools.route('/media-download/<path:filename>')
def download_file(filename):
    """Download a media file"""
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)