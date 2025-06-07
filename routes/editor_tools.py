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

@editor_tools.route('/editor-download/<path:filename>')
def download_file(filename):
    """Download a file from the editor"""
    directory = os.path.dirname(filename)
    file = os.path.basename(filename)
    return send_from_directory(os.path.join(current_app.config['TEMP_FOLDER'], directory), file, as_attachment=True)