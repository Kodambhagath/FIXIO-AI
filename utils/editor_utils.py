import os
import logging
from PIL import Image, ImageDraw, ImageFont
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import base64
from utils.file_handler import format_file_size

def edit_certificate(input_path, output_path, edit_config):
    """
    Edit a certificate (PDF or image) with text, signatures, and logos.
    
    Args:
        input_path (str): Path to input file (PDF or image)
        output_path (str): Path to save the edited file
        edit_config (dict): Configuration for edits including:
            - text_edits: List of text edits with position and content
            - signature: Base64 encoded signature image
            - signature_position: Position to place signature
            - logo_path: Path to logo image file
            - logo_position: Position to place logo
    
    Returns:
        tuple: (success, message)
    """
    try:
        file_ext = os.path.splitext(input_path)[1].lower()
        
        if file_ext == '.pdf':
            return edit_pdf_certificate(input_path, output_path, edit_config)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return edit_image_certificate(input_path, output_path, edit_config)
        else:
            return False, "Unsupported file format. Only PDF and images (PNG, JPG) are supported."
    
    except Exception as e:
        error_msg = f"Error editing certificate: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def edit_pdf_certificate(input_path, output_path, edit_config):
    """Edit a PDF certificate"""
    try:
        # Read the existing PDF
        pdf_reader = PyPDF2.PdfReader(open(input_path, 'rb'))
        pdf_writer = PyPDF2.PdfWriter()
        
        # Process each page (usually just one for certificates)
        for page_num in range(len(pdf_reader.pages)):
            # Get the page
            page = pdf_reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Create a PDF overlay for edits
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            
            # Add text edits
            for text_edit in edit_config.get('text_edits', []):
                text = text_edit.get('text', '')
                x = float(text_edit.get('x', 0)) * page_width
                y = page_height - float(text_edit.get('y', 0)) * page_height  # Flip Y coordinate
                font_size = int(text_edit.get('font_size', 12))
                color = text_edit.get('color', '#000000')
                
                # Convert hex color to RGB
                r, g, b = tuple(int(color.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4))
                
                can.setFont("Helvetica", font_size)
                can.setFillColorRGB(r, g, b)
                can.drawString(x, y, text)
            
            # Add signature if provided
            if edit_config.get('signature'):
                sig_data = edit_config['signature'].split(',')[1] if ',' in edit_config['signature'] else edit_config['signature']
                signature_image = Image.open(io.BytesIO(base64.b64decode(sig_data)))
                
                # Get signature position
                sig_pos = edit_config.get('signature_position', {})
                sig_x = float(sig_pos.get('x', 0.5)) * page_width
                sig_y = float(sig_pos.get('y', 0.7)) * page_height
                sig_width = float(sig_pos.get('width', 0.2)) * page_width
                
                # Scale signature
                sig_height = int(sig_width * signature_image.height / signature_image.width)
                
                # Save signature to temporary file
                temp_sig_path = output_path + "_sig_temp.png"
                signature_image.save(temp_sig_path)
                
                # Draw signature on canvas
                can.drawImage(temp_sig_path, sig_x, page_height - sig_y - sig_height, 
                             width=sig_width, height=sig_height)
                
                # Clean up temporary file
                try:
                    os.remove(temp_sig_path)
                except:
                    pass
            
            # Add logo if provided
            if edit_config.get('logo_path') and os.path.exists(edit_config['logo_path']):
                logo_image = Image.open(edit_config['logo_path'])
                
                # Get logo position
                logo_pos = edit_config.get('logo_position', {})
                logo_x = float(logo_pos.get('x', 0.1)) * page_width
                logo_y = float(logo_pos.get('y', 0.1)) * page_height
                logo_width = float(logo_pos.get('width', 0.15)) * page_width
                
                # Scale logo
                logo_height = int(logo_width * logo_image.height / logo_image.width)
                
                # Draw logo on canvas
                can.drawImage(edit_config['logo_path'], logo_x, page_height - logo_y - logo_height, 
                             width=logo_width, height=logo_height)
            
            can.save()
            
            # Move to the beginning of the BytesIO buffer
            packet.seek(0)
            overlay = PyPDF2.PdfReader(packet)
            
            # Merge the overlay with the original page
            page.merge_page(overlay.pages[0])
            
            # Add the page to the output PDF
            pdf_writer.add_page(page)
        
        # Write the output PDF
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        
        return True, "Certificate edited successfully"
    
    except Exception as e:
        error_msg = f"Error editing PDF certificate: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def edit_image_certificate(input_path, output_path, edit_config):
    """Edit an image certificate"""
    try:
        # Open the image
        img = Image.open(input_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Add text edits
        for text_edit in edit_config.get('text_edits', []):
            text = text_edit.get('text', '')
            x = int(float(text_edit.get('x', 0)) * width)
            y = int(float(text_edit.get('y', 0)) * height)
            font_size = int(text_edit.get('font_size', 24))
            color = text_edit.get('color', '#000000')
            
            # Try to use a font or fall back to default
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Draw the text
            draw.text((x, y), text, fill=color, font=font)
        
        # Add signature if provided
        if edit_config.get('signature'):
            sig_data = edit_config['signature'].split(',')[1] if ',' in edit_config['signature'] else edit_config['signature']
            signature_image = Image.open(io.BytesIO(base64.b64decode(sig_data)))
            
            # Get signature position
            sig_pos = edit_config.get('signature_position', {})
            sig_x = int(float(sig_pos.get('x', 0.5)) * width)
            sig_y = int(float(sig_pos.get('y', 0.7)) * height)
            sig_width = int(float(sig_pos.get('width', 0.2)) * width)
            
            # Scale signature
            sig_height = int(sig_width * signature_image.height / signature_image.width)
            signature_image = signature_image.resize((sig_width, sig_height))
            
            # Paste signature onto image
            if signature_image.mode == 'RGBA':
                img.paste(signature_image, (sig_x, sig_y), signature_image)
            else:
                img.paste(signature_image, (sig_x, sig_y))
        
        # Add logo if provided
        if edit_config.get('logo_path') and os.path.exists(edit_config['logo_path']):
            logo_image = Image.open(edit_config['logo_path'])
            if logo_image.mode != 'RGBA':
                logo_image = logo_image.convert('RGBA')
            
            # Get logo position
            logo_pos = edit_config.get('logo_position', {})
            logo_x = int(float(logo_pos.get('x', 0.1)) * width)
            logo_y = int(float(logo_pos.get('y', 0.1)) * height)
            logo_width = int(float(logo_pos.get('width', 0.15)) * width)
            
            # Scale logo
            logo_height = int(logo_width * logo_image.height / logo_image.width)
            logo_image = logo_image.resize((logo_width, logo_height))
            
            # Paste logo onto image
            img.paste(logo_image, (logo_x, logo_y), logo_image)
        
        # Save the edited image
        img.save(output_path)
        
        return True, "Certificate edited successfully"
    
    except Exception as e:
        error_msg = f"Error editing image certificate: {str(e)}"
        logging.error(error_msg)
        return False, error_msg