from flask import Blueprint, render_template, request, jsonify

assistant_bp = Blueprint('assistant_bp', __name__)

@assistant_bp.route('/assistant')
def assistant():
    return render_template('ai_assistant.html')

@assistant_bp.route('/assistant/ask', methods=['POST'])
def ask_assistant():
    query = request.form.get('query', '').lower()
    
    # Simple keyword-based assistant
    response = get_assistant_response(query)
    
    return jsonify({
        'response': response
    })

def get_assistant_response(query):
    """
    Simple keyword-based assistant that provides responses based on detected keywords in the query.
    """
    # PDF related queries
    if any(keyword in query for keyword in ['merge pdf', 'combine pdf', 'join pdf']):
        return """
            To merge PDF files using Fixio:
            1. Go to the PDF Merger tool
            2. Upload multiple PDF files
            3. Arrange them in the desired order
            4. Click "Merge PDFs"
            5. Download your combined PDF file
            
            The PDF Merger tool can handle multiple files and preserves the quality of your documents.
        """
    
    elif any(keyword in query for keyword in ['watermark', 'remove watermark']):
        return """
            To remove watermarks from PDF files:
            1. Go to the Watermark Remover tool
            2. Upload your PDF file
            3. The tool will attempt to remove visible watermarks
            4. Download the processed PDF
            
            Note that complex or embedded watermarks may not be completely removed.
        """
    
    # Image related queries
    elif any(keyword in query for keyword in ['convert image', 'jpg to png', 'png to jpg']):
        return """
            To convert images between formats:
            1. Go to the Image Converter tool
            2. Upload your image file
            3. Select the target format (PNG, JPG, etc.)
            4. Click "Convert Image"
            5. Preview and download the converted image
            
            For web graphics with transparency, PNG is recommended. For photos, JPG usually provides smaller file sizes.
        """
    
    elif any(keyword in query for keyword in ['background', 'remove background', 'transparent']):
        return """
            To remove the background from an image:
            1. Go to the Background Remover tool
            2. Upload your image (best with clear subject separation)
            3. Our AI will automatically detect and remove the background
            4. Download the resulting image with transparent background (PNG format)
            
            This is perfect for product photos, portraits, or creating graphics for presentations.
        """
    
    elif any(keyword in query for keyword in ['compress', 'reduce size', 'smaller image']):
        return """
            To compress an image and reduce its file size:
            1. Go to the Image Compressor tool
            2. Upload your image
            3. Adjust the compression level slider (higher for better quality, lower for smaller size)
            4. Click "Compress Image"
            5. Preview the results and download the compressed image
            
            This is useful for web uploads, email attachments, or saving storage space.
        """
    
    # Document related queries
    elif any(keyword in query for keyword in ['convert document', 'word to pdf', 'excel to pdf']):
        return """
            To convert between document formats:
            1. Go to the Document Converter tool
            2. Upload your document (DOCX, DOC, XLSX, TXT, etc.)
            3. Select the target format
            4. Click "Convert Document"
            5. Download the converted file
            
            Fixio supports conversions between various document formats while preserving formatting.
        """
    
    # Size conversion queries
    elif any(keyword in query for keyword in ['size convert', 'mb to gb', 'gb to mb', 'convert file size']):
        return """
            To convert between file size units:
            1. Go to the MB/GB Converter tool
            2. Enter the value you want to convert
            3. Select the source unit (Bytes, KB, MB, GB, or TB)
            4. Select the target unit you want to convert to
            5. Click "Convert" to see the result
            
            This tool helps you understand file sizes and storage requirements.
        """
    
    # Best format questions
    elif any(keyword in query for keyword in ['best format', 'which format']):
        if 'image' in query or 'picture' in query or 'photo' in query:
            return """
                Best image formats depend on your needs:
                
                - JPG/JPEG: Best for photographs and complex images. Smaller file sizes but lossy compression.
                
                - PNG: Best for graphics, logos, and images needing transparency. Lossless quality but larger file sizes.
                
                - GIF: Best for simple animations with limited colors.
                
                For web use, JPG is generally best for photos, while PNG is better for graphics with transparent backgrounds or text.
            """
        elif 'document' in query:
            return """
                Best document formats depend on your purpose:
                
                - PDF: Best for sharing documents that shouldn't be easily edited, preserves exact formatting across all devices.
                
                - DOCX: Best for documents you'll continue to edit, using Microsoft Word or compatible programs.
                
                - TXT: Best for plain text without formatting, maximum compatibility.
                
                For official documents or final versions, PDF is usually the preferred format.
            """
    
    # General help
    elif any(keyword in query for keyword in ['help', 'tool', 'feature', 'what can you do']):
        return """
            Fixio offers several tools to help with file processing:
            
            - PDF Tools: Merge PDFs, Remove Watermarks
            - Image Tools: Convert Images, Remove Backgrounds, Compress Images
            - Document Tools: Convert between different document formats
            - Utilities: MB/GB Converter
            
            Select a tool from the navigation menu to get started, or ask me specific questions about any tool!
        """
    
    # Default response
    else:
        return """
            I'm here to help you with Fixio's file processing tools. You can ask me about:
            
            - How to use specific tools like the PDF Merger or Background Remover
            - Which file formats to use for different purposes
            - Tips for reducing file sizes
            - General file processing advice
            
            Try asking something like "How do I merge PDFs?" or "What's the best image format for photos?"
        """
