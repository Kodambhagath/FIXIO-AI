import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, jsonify
from werkzeug.utils import secure_filename
import uuid
import json
from utils.file_handler import allowed_file
from utils.editor_utils import edit_certificate
from flask_login import login_required, current_user
from models import db, FileOperation

editor_tools = Blueprint('editor_tools', __name__)

@editor_tools.route('/certificate-editor')
def certificate_editor():
    """Render the certificate editor page"""
    return render_template('editor/certificate_editor.html')

@editor_tools.route('/certificate-editor', methods=['POST'])
@login_required
def certificate_editor_process():
    """Process certificate editing"""
    if 'file' not in request.files:
        flash('Please select a file to upload', 'danger')
        return redirect(request.url)
        
    # Add file size validation
    file = request.files['file']
    if file.content_length and file.content_length > 10 * 1024 * 1024:  # 10MB limit
        flash('File size too large. Please upload a file smaller than 10MB.', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'certificate'):
        flash('File type not allowed. Please upload a PDF or image file (PNG, JPG).', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Get edit configurations
    edit_config = {
        'text_edits': json.loads(request.form.get('text_edits', '[]')),
        'signature': request.form.get('signature_data', None),
        'signature_position': json.loads(request.form.get('signature_position', '{}')),
        'logo_position': json.loads(request.form.get('logo_position', '{}'))
    }
    
    # Check if a logo was uploaded
    logo_file = None
    if 'logo_file' in request.files:
        logo_file = request.files['logo_file']
        if logo_file and logo_file.filename != '' and allowed_file(logo_file.filename, 'image'):
            logo_filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(upload_path, logo_filename)
            logo_file.save(logo_path)
            edit_config['logo_path'] = logo_path
    
    # Set output filename
    file_ext = os.path.splitext(filename)[1].lower()
    output_filename = request.form.get('output_filename', f'edited_certificate{file_ext}')
    if not output_filename.lower().endswith(file_ext):
        output_filename += file_ext
        
    output_filename = secure_filename(output_filename)
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Edit the certificate
        success, message = edit_certificate(file_path, output_path, edit_config)
        
        # Store operation in database
        if current_user.is_authenticated:
            operation = FileOperation(
                user_id=current_user.id,
                operation_type='certificate_edit',
                original_filename=filename,
                result_filename=output_filename,
                input_path=file_path,
                output_path=output_path,
                parameters=f"Text edits: {len(edit_config['text_edits'])}, " +
                           f"Signature: {'Yes' if edit_config['signature'] else 'No'}, " +
                           f"Logo: {'Yes' if logo_file and logo_file.filename != '' else 'No'}",
                status='completed' if success else 'failed',
                error_message='' if success else message
            )
            db.session.add(operation)
            db.session.commit()
        
        if success:
            flash('Certificate edited successfully!', 'success')
            # Pass the result file path for download
            result_file = os.path.join(operation_id, output_filename)
            return render_template('editor/certificate_editor.html', result_file=result_file)
        else:
            flash(f'Error editing certificate: {message}', 'danger')
            return redirect(request.url)
            
    except Exception as e:
        flash(f'Error processing certificate: {str(e)}', 'danger')
        return redirect(request.url)

@editor_tools.route('/editor-download/<path:filename>')
def download_file(filename):
    """Download a file from the editor"""
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)