import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
import uuid
from utils.file_handler import allowed_file
from utils.pdf_utils import merge_pdfs, remove_watermark, recover_pdf_pages
from flask_login import login_required, current_user
from models import db, FileOperation

pdf_tools = Blueprint('pdf_tools', __name__)

@pdf_tools.route('/pdf-merger')
def pdf_merger():
    return render_template('pdf_merger.html')

@pdf_tools.route('/pdf-merger', methods=['POST'])
def pdf_merger_process():
    pdf_files = []
    
    # Create a unique directory for this batch
    batch_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], batch_id)
    os.makedirs(upload_path, exist_ok=True)
    
    # Check if using bulk upload or individual files
    if request.form.get('use_multiple_upload') == '1':
        # Bulk upload method
        if 'files' not in request.files:
            flash('No files selected for bulk upload', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            flash('No files selected for bulk upload', 'danger')
            return redirect(request.url)
        
        for file in files:
            if file and allowed_file(file.filename, 'pdf'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_path, filename)
                file.save(file_path)
                pdf_files.append(file_path)
            else:
                flash(f'File {file.filename} is not a valid PDF', 'danger')
    else:
        # Individual file upload method
        file_count = int(request.form.get('file_count', 2))
        
        # Enforce min/max constraints
        if file_count < 2:
            file_count = 2
        elif file_count > 20:
            file_count = 20
        
        # Process each individual file
        for i in range(1, file_count + 1):
            file_key = f'file_{i}'
            
            if file_key in request.files:
                file = request.files[file_key]
                
                if file and file.filename != '' and allowed_file(file.filename, 'pdf'):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_path, filename)
                    file.save(file_path)
                    pdf_files.append(file_path)
                elif file.filename != '':
                    flash(f'File {i} ({file.filename}) is not a valid PDF', 'danger')
            else:
                flash(f'File {i} is missing', 'danger')
    
    if not pdf_files:
        flash('No valid PDF files uploaded', 'danger')
        return redirect(request.url)
    
    if len(pdf_files) < 2:
        flash('At least two valid PDF files are required for merging', 'danger')
        return redirect(request.url)
    
    output_filename = request.form.get('output_filename', 'merged_document.pdf')
    if not output_filename.lower().endswith('.pdf'):
        output_filename += '.pdf'
    
    output_filename = secure_filename(output_filename)
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Add the operation to database if user is authenticated
        if current_user.is_authenticated:
            # Save the operation in the database
            operation = FileOperation(
                user_id=current_user.id,
                operation_type='pdf_merge',
                original_filename=','.join([os.path.basename(f) for f in pdf_files]),
                result_filename=output_filename,
                parameters=f"Number of files: {len(pdf_files)}",
                status='pending'
            )
            db.session.add(operation)
            db.session.commit()
        
        # Merge the PDFs
        merge_pdfs(pdf_files, output_path)
        
        # Update operation status if user is authenticated
        if current_user.is_authenticated:
            operation.status = 'completed'
            operation.completed_at = datetime.utcnow()
            db.session.commit()
        
        flash(f'Successfully merged {len(pdf_files)} PDF files!', 'success')
        
        # Pass the result file path for download
        result_file = os.path.join(batch_id, output_filename)
        return render_template('pdf_merger.html', result_file=result_file)
    
    except Exception as e:
        # Update operation status if user is authenticated
        if current_user.is_authenticated:
            operation.status = 'failed'
            operation.error_message = str(e)
            db.session.commit()
        
        flash(f'Error merging PDFs: {str(e)}', 'danger')
        return redirect(request.url)

@pdf_tools.route('/watermark-remover')
def watermark_remover():
    return render_template('watermark_remover.html')

@pdf_tools.route('/watermark-remover', methods=['POST'])
def watermark_remover_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'pdf'):
        flash('File type not allowed. Please upload a PDF file.', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    output_filename = request.form.get('output_filename', 'clean_document.pdf')
    if not output_filename.lower().endswith('.pdf'):
        output_filename += '.pdf'
        
    output_filename = secure_filename(output_filename)
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Remove watermark from PDF
        success = remove_watermark(file_path, output_path)
        
        if success:
            flash('Watermark removal process completed!', 'success')
        else:
            flash('Processed the PDF, but may not have removed all watermarks.', 'warning')
        
        # Pass the result file path for download
        result_file = os.path.join(operation_id, output_filename)
        return render_template('watermark_remover.html', result_file=result_file)
    
    except Exception as e:
        flash(f'Error processing PDF: {str(e)}', 'danger')
        return redirect(request.url)

@pdf_tools.route('/pdf-pages-recovery')
def pdf_pages_recovery():
    """Render the PDF pages recovery page"""
    return render_template('pdf_pages_recovery.html')

@pdf_tools.route('/pdf-pages-recovery', methods=['POST'])
@login_required
def pdf_pages_recovery_process():
    """Process PDF page recovery"""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'pdf'):
        flash('File type not allowed. Please upload a PDF file.', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    output_filename = request.form.get('output_filename', 'recovered_document.pdf')
    if not output_filename.lower().endswith('.pdf'):
        output_filename += '.pdf'
        
    output_filename = secure_filename(output_filename)
    output_path = os.path.join(upload_path, output_filename)
    
    # Get page numbers to extract if specified
    page_range = request.form.get('page_range', '')
    
    try:
        # Extract pages from PDF
        success, message, total_pages, recovered_pages = recover_pdf_pages(file_path, output_path, page_range)
        
        # Store operation in database
        if current_user.is_authenticated:
            operation = FileOperation(
                user_id=current_user.id,
                operation_type='pdf_pages_recovery',
                original_filename=filename,
                result_filename=output_filename,
                input_path=file_path,
                output_path=output_path,
                parameters=f"Page Range: {page_range if page_range else 'All'}",
                status='completed' if success else 'failed',
                error_message='' if success else message
            )
            db.session.add(operation)
            db.session.commit()
        
        if success:
            flash(f'PDF recovery completed! Recovered {recovered_pages} of {total_pages} pages.', 'success')
            # Pass the result file path for download
            result_file = os.path.join(operation_id, output_filename)
            return render_template('pdf_pages_recovery.html', result_file=result_file)
        else:
            flash(f'Error recovering PDF pages: {message}', 'danger')
            return redirect(request.url)
            
    except Exception as e:
        flash(f'Error processing PDF: {str(e)}', 'danger')
        return redirect(request.url)

@pdf_tools.route('/pdf-download/<path:filename>')
def download_file(filename):
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)
