import os
import random
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
import uuid
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from utils.file_handler import allowed_file
from utils.doc_utils import convert_document

doc_tools = Blueprint('doc_tools', __name__)

@doc_tools.route('/doc-converter')
def doc_converter():
    return render_template('doc_converter.html')

@doc_tools.route('/doc-converter', methods=['POST'])
def doc_converter_process():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if not allowed_file(file.filename, 'document'):
        flash('File type not allowed. Please upload a valid document file.', 'danger')
        return redirect(request.url)
    
    # Create a unique directory for this operation
    operation_id = str(uuid.uuid4())
    upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
    os.makedirs(upload_path, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    target_format = request.form.get('target_format', 'pdf').lower()
    
    # Create output filename with new extension
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}.{target_format}"
    output_path = os.path.join(upload_path, output_filename)
    
    try:
        # Convert document
        success, message = convert_document(file_path, output_path, target_format)
        
        if success:
            flash('Document converted successfully!', 'success')
            # Pass the result file path for download
            result_file = os.path.join(operation_id, output_filename)
            return render_template('doc_converter.html', result_file=result_file)
        else:
            flash(f'Failed to convert document: {message}', 'danger')
            return redirect(request.url)
    
    except Exception as e:
        flash(f'Error converting document: {str(e)}', 'danger')
        return redirect(request.url)

@doc_tools.route('/doc-download/<path:filename>')
def download_file(filename):
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)


@doc_tools.route('/ai-excel-editor')
def ai_excel_editor():
    return render_template('ai_excel_editor.html')

@doc_tools.route('/ai-excel-editor', methods=['POST'])
def ai_excel_editor_process():
    try:
        command = request.form.get('command', '').lower()
        if not command:
            flash('Please provide a command', 'warning')
            return redirect(request.url)

        # Create unique directory
        operation_id = str(uuid.uuid4())
        upload_path = os.path.join(current_app.config['TEMP_FOLDER'], operation_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # Initialize DataFrame
        df = pd.DataFrame()
        
        # Handle file if provided
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if allowed_file(file.filename, 'excel'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_path, filename)
                file.save(file_path)
                df = pd.read_excel(file_path)
            else:
                flash('Invalid file type. Please upload Excel files only.', 'danger')
                return redirect(request.url)
        else:
            filename = 'new_sheet.xlsx'
            
        try:
            # Process commands and generate data
            if 'marksheet' in command or 'student' in command:
                students = ['Student ' + str(i+1) for i in range(5)]
                df = pd.DataFrame({
                    'Student Name': students,
                    'Age': [18 + i for i in range(5)],
                    'Math': [random.randint(60, 100) for _ in range(5)],
                    'Science': [random.randint(60, 100) for _ in range(5)],
                    'English': [random.randint(60, 100) for _ in range(5)]
                })
                df['Average'] = df[['Math', 'Science', 'English']].mean(axis=1).round(2)
            
            elif 'sales' in command or 'report' in command:
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
                sales = [random.randint(5000, 15000) for _ in range(5)]
                expenses = [random.randint(3000, 8000) for _ in range(5)]
                profits = [s - e for s, e in zip(sales, expenses)]
                
                df = pd.DataFrame({
                    'Month': months,
                    'Sales': sales,
                    'Expenses': expenses,
                    'Profit': profits
                })
        except Exception as e:
            flash(f'Error generating data: {str(e)}', 'danger')
            return redirect(request.url)
        
        # Process natural language commands
        command = command.lower()
        
        if 'add names under' in command:
            category = command.split('under')[1].split(':')[0].strip()
            names = command.split(':')[1].strip().split(',')
            new_data = pd.DataFrame({category: [name.strip() for name in names]})
            df = pd.concat([df, new_data], ignore_index=True)
            
        elif 'make a table of' in command:
            # Extract table structure from command
            content = command.split('make a table of')[1].strip()
            if 'and their' in content:
                items = content.split('and their')[0].strip()
                attributes = content.split('and their')[1].strip()
                df = pd.DataFrame(columns=[items.title(), attributes.title()])
                
        elif 'sort' in command:
            column = command.split('by')[1].strip()
            df = df.sort_values(by=column)
            
        elif 'filter' in command:
            condition = command.split('where')[1].strip()
            df = df.query(condition)
        
        # If DataFrame is empty after processing, create default structure
        if df.empty:
            df = pd.DataFrame({
                'Name': ['Example'],
                'Age': [25],
                'Marks': [85]
            })
            flash('Created default sheet structure', 'info')

        # Save processed file with styling
        output_filename = f"processed_{filename}"
        output_path = os.path.join(upload_path, output_filename)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            # Apply styling
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Style header
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
            
        if os.path.exists(output_path):
            return send_from_directory(upload_path, output_filename, as_attachment=True)
        else:
            flash('Failed to generate Excel file', 'danger')
            return redirect(request.url)
            
    except Exception as e:
        flash(f'Error processing Excel file: {str(e)}', 'danger')
        return redirect(request.url)
