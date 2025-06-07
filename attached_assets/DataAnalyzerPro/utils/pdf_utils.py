import os
import PyPDF2
import logging
from datetime import datetime

def merge_pdfs(input_paths, output_path):
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        input_paths (list): List of paths to input PDF files
        output_path (str): Path to save the merged PDF
    
    Returns:
        bool: True if successful, False otherwise
    """
    merger = PyPDF2.PdfMerger()
    
    try:
        # Add each PDF to the merger
        for path in input_paths:
            merger.append(path)
        
        # Write the merged PDF to the output file
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        return True
    
    except Exception as e:
        logging.error(f"Error merging PDFs: {str(e)}")
        raise
    
    finally:
        # Close the merger
        merger.close()

def remove_watermark(input_path, output_path):
    """
    Attempt to remove watermarks from a PDF document.
    This function uses a simple approach to remove annotations that might be watermarks.
    
    Args:
        input_path (str): Path to input PDF file
        output_path (str): Path to save the processed PDF
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Open the input PDF
        with open(input_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            
            # Process each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                
                # Attempt to remove annotations (some watermarks are added as annotations)
                if '/Annots' in page:
                    del page['/Annots']
                
                # Add the processed page to the writer
                writer.add_page(page)
            
            # Write the processed PDF to the output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
        
        return True
    
    except Exception as e:
        logging.error(f"Error removing watermark: {str(e)}")
        raise

def recover_pdf_pages(input_path, output_path, page_range=''):
    """
    Extract and recover pages from a PDF document.
    
    Args:
        input_path (str): Path to input PDF file
        output_path (str): Path to save the processed PDF
        page_range (str): Range of pages to extract (e.g., '1-5,8,11-13')
                         If empty, all pages will be extracted
    
    Returns:
        tuple: (success, message, total_pages, recovered_pages)
    """
    try:
        # Open the input PDF
        with open(input_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            
            total_pages = len(reader.pages)
            recovered_pages = 0
            
            # Process specified pages or all pages if no range is provided
            if not page_range:
                # Extract all pages
                for page_num in range(total_pages):
                    try:
                        page = reader.pages[page_num]
                        writer.add_page(page)
                        recovered_pages += 1
                    except Exception as e:
                        logging.error(f"Error processing page {page_num + 1}: {str(e)}")
            else:
                # Parse the page range (e.g., '1-5,8,11-13')
                pages_to_extract = []
                parts = page_range.split(',')
                
                for part in parts:
                    if '-' in part:
                        # Handle range (e.g., '1-5')
                        start, end = part.split('-')
                        try:
                            start_num = int(start.strip())
                            end_num = int(end.strip())
                            # Adjust for 0-based indexing
                            pages_to_extract.extend(range(start_num - 1, end_num))
                        except ValueError:
                            # Skip invalid ranges
                            continue
                    else:
                        # Handle single page (e.g., '8')
                        try:
                            page_num = int(part.strip())
                            # Adjust for 0-based indexing
                            pages_to_extract.append(page_num - 1)
                        except ValueError:
                            # Skip invalid page numbers
                            continue
                
                # Extract specified pages
                for page_idx in pages_to_extract:
                    if 0 <= page_idx < total_pages:
                        try:
                            page = reader.pages[page_idx]
                            writer.add_page(page)
                            recovered_pages += 1
                        except Exception as e:
                            logging.error(f"Error processing page {page_idx + 1}: {str(e)}")
            
            # Write the processed PDF to the output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
        
        return True, "PDF pages successfully recovered", total_pages, recovered_pages
    
    except Exception as e:
        error_msg = f"Error recovering PDF pages: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, 0, 0


def protect_pdf(input_path, output_path, password='', time_lock=None, view_only=False):
    """
    Add protection to a PDF document.
    
    Args:
        input_path (str): Path to input PDF file
        output_path (str): Path to save the protected PDF
        password (str): Password to encrypt the PDF (if protection_type is 'password')
        time_lock (datetime): Date until which the PDF is locked (if protection_type is 'time_lock')
        view_only (bool): Whether to set the PDF as view-only (if protection_type is 'view_only')
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Open the input PDF
        reader = PyPDF2.PdfReader(input_path)
        writer = PyPDF2.PdfWriter()
        
        # Copy all pages from the original PDF
        for page in reader.pages:
            writer.add_page(page)
        
        # Apply password protection if specified
        if password:
            writer.encrypt(password)
            
        # Set document metadata for time lock
        if time_lock:
            # Add custom metadata for time lock
            # Note: This is metadata only, actual enforcement would need a specialized PDF viewer
            writer.add_metadata({
                '/TimeRestriction': time_lock.strftime('%Y-%m-%d'),
                '/RestrictedUntil': time_lock.strftime('%Y-%m-%d'),
            })
        
        # Set restrictions for view-only mode
        if view_only:
            # These permissions will be applied if PDF is encrypted
            # So we set a default encryption if none is provided
            if not password:
                # Use a random password for encryption that's not exposed to the user
                import uuid
                random_password = str(uuid.uuid4())
                
                # Apply encryption with restrictions
                writer.encrypt(
                    user_password='',  # Empty user password allows opening
                    owner_password=random_password,  # Owner password for changing permissions
                    use_128bit=True
                )
                
                # Set permissions to restrict editing, printing, etc.
                # Only allow reading
                permissions = 0
                writer._encrypt_dictionary['/P'] = permissions
            else:
                # Apply restrictions with user's password
                writer.encrypt(
                    user_password=password,
                    owner_password=password,
                    use_128bit=True
                )
                
                # Set permissions to restrict editing, printing, etc.
                # Only allow reading
                permissions = 0
                writer._encrypt_dictionary['/P'] = permissions
        
        # Write the protected PDF to the output file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Determine the message based on the protection type
        if password:
            message = "Password protection added successfully"
        elif time_lock:
            message = f"Time lock set until {time_lock.strftime('%Y-%m-%d')}"
        elif view_only:
            message = "View-only restrictions applied successfully"
        else:
            message = "PDF processed successfully"
        
        return True, message
        
    except Exception as e:
        error_msg = f"Error protecting PDF: {str(e)}"
        logging.error(error_msg)
        return False, error_msg
