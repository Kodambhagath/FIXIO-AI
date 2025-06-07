import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
import uuid
from utils.file_handler import allowed_file, get_file_size_str
from utils.image_utils import convert_image, remove_background, compress_image

image_tools = Blueprint('image_tools', __name__)

@image_tools.route('/image-converter')
def image_converter():
    return render_template('image_converter.html')

@image_tools.route('/image-converter', methods=['POST'])
def image_converter_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'image'):
        flash('File type not allowed. Please upload a valid image file.', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    target_format = request.form.get('target_format', 'png').lower()
    
    # Create output filename with new extension
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}.{target_format}"
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Convert image
        success = convert_image(file_path, output_path, target_format)
        
        if success:
            flash('Image converted successfully!', 'success')
            # Pass the result file path for download and preview
            result_file = os.path.join(operation_id, output_filename)
            return render_template('image_converter.html', result_file=result_file)
        else:
            flash('Failed to convert image. Please try a different format or image.', 'danger')
            return redirect(request.url)
    
    except Exception as e:
        flash(f'Error converting image: {str(e)}', 'danger')
        return redirect(request.url)

@image_tools.route('/background-remover')
def background_remover():
    return render_template('background_remover.html')

@image_tools.route('/background-remover', methods=['POST'])
def background_remover_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'image'):
        flash('File type not allowed. Please upload a valid image file.', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Create output filename with PNG extension for transparency
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}_nobg.png"
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Remove background from image
        success, error_message = remove_background(file_path, output_path)
        
        if success:
            flash('Background removed successfully!', 'success')
            # Pass the result file path for download and preview
            result_file = os.path.join(operation_id, output_filename)
            original_file = os.path.join(operation_id, filename)
            return render_template('background_remover.html', result_file=result_file, original_file=original_file)
        else:
            flash(f'Failed to remove background: {error_message}', 'danger')
            return redirect(request.url)
    
    except Exception as e:
        flash(f'Error removing background: {str(e)}', 'danger')
        return redirect(request.url)

@image_tools.route('/image-compressor')
def image_compressor():
    return render_template('image_compressor.html')

@image_tools.route('/image-compressor', methods=['POST'])
def image_compressor_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'image'):
        flash('File type not allowed. Please upload a valid image file.', 'danger')
        return redirect(request.url)
    
    # Get compression quality
    quality = int(request.form.get('quality', 70))
    if quality < 1 or quality > 100:
        quality = 70
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Create output filename
    base_name, ext = os.path.splitext(filename)
    output_filename = f"{base_name}_compressed{ext}"
    output_path = os.path.join(upload_path, output_filename)
    
    # Compress image
    original_size, compressed_size, reduction_percent = compress_image(file_path, output_path, quality)
    
    if original_size is None or compressed_size is None:
        flash('Error compressing image. Please try a different image.', 'danger')
        return redirect(request.url)
    
    flash('Image compressed successfully!', 'success')
    # Pass the result file path and size information
    result_file = os.path.join(operation_id, output_filename)
    original_file = os.path.join(operation_id, filename)
    
    return render_template(
        'image_compressor.html', 
        result_file=result_file, 
        original_file=original_file,
        original_size=original_size,
        compressed_size=compressed_size,
        reduction_percent=reduction_percent
    )

@image_tools.route('/image-download/<path:filename>')
def download_file(filename):
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)

@image_tools.route('/image-preview/<path:filename>')
def preview_image(filename):
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file)
