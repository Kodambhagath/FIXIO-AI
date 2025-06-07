import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from flask_login import login_required, current_user

from utils.pdf_utils import protect_pdf
from utils.file_handler import allowed_file, get_file_size_str, clean_temp_files
from app import db
from models import FileOperation

# Create blueprint
security_tools = Blueprint('security_tools', __name__)

# Ensure temp directory exists
os.makedirs('temp', exist_ok=True)
os.makedirs('uploads', exist_ok=True)


@security_tools.route('/pdf/protect', methods=['GET', 'POST'])
def pdf_protect():
    """Render the PDF protection page"""
    if request.method == 'GET':
        return render_template('security/pdf_protect.html')
    
    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, 'pdf'):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4()}_{original_filename}"
        input_path = os.path.join('temp', filename)
        
        # Save the uploaded file
        file.save(input_path)
        
        # Get protection options
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        protection_type = request.form.get('protection_type', 'password')
        
        if protection_type == 'password' and (not password or password != confirm_password):
            flash('Passwords do not match or are empty', 'danger')
            return redirect(request.url)
        
        # Generate output path
        output_filename = f"protected_{filename}"
        output_path = os.path.join('temp', output_filename)
        
        # Process file
        time_lock = None
        if protection_type == 'time_lock':
            time_lock = request.form.get('time_lock_date', '')
            try:
                time_lock = datetime.strptime(time_lock, '%Y-%m-%d')
            except:
                flash('Invalid date format', 'danger')
                return redirect(request.url)
        
        view_only = protection_type == 'view_only'
        
        success, message = protect_pdf(
            input_path=input_path, 
            output_path=output_path, 
            password=password,
            time_lock=time_lock,
            view_only=view_only
        )
        
        if success:
            # Store file operation in database if user is logged in
            if current_user.is_authenticated:
                file_operation = FileOperation(
                    user_id=current_user.id,
                    operation_type='pdf_protect',
                    original_filename=original_filename,
                    result_filename=output_filename,
                    input_path=input_path,
                    output_path=output_path,
                    parameters=f"protection_type={protection_type}",
                    status='completed',
                    completed_at=datetime.utcnow()
                )
                db.session.add(file_operation)
                db.session.commit()
            
            # Store filename in session for download
            session['download_file'] = output_filename
            
            # Redirect to download page
            flash('PDF protected successfully', 'success')
            return redirect(url_for('security_tools.download_file', filename=output_filename))
        else:
            flash(f'Failed to protect PDF: {message}', 'danger')
            return redirect(request.url)
    else:
        flash('Invalid file type. Please upload a PDF file.', 'danger')
        return redirect(request.url)


@security_tools.route('/download/<filename>')
def download_file(filename):
    """Download a security-processed file"""
    return send_from_directory('temp', filename, as_attachment=True)