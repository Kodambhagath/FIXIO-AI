import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from models import db, User

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fixio_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['TEMP_FOLDER'] = 'temp'
app.config['ALLOWED_EXTENSIONS'] = {
    'pdf': ['pdf'],
    'image': ['png', 'jpg', 'jpeg', 'gif'],
    'document': ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt'],
    'excel': ['xlsx', 'xls', 'csv']
}

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300
}

# Update allowed extensions to include audio and certificates
app.config['ALLOWED_EXTENSIONS'].update({
    'audio': ['mp3', 'wav', 'ogg', 'aac', 'flac'],
    'certificate': ['pdf', 'png', 'jpg', 'jpeg']
})

# Initialize database
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Set the login view

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Ensure upload and temp directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Register blueprints
from routes.pdf_tools import pdf_tools
from routes.image_tools import image_tools
from routes.doc_tools import doc_tools
from routes.utility_tools import utility_tools
from routes.assistant import assistant_bp

app.register_blueprint(pdf_tools)
app.register_blueprint(image_tools)
app.register_blueprint(doc_tools)
app.register_blueprint(utility_tools)
app.register_blueprint(assistant_bp)

# Create auth blueprint and register it
from routes.auth import auth
app.register_blueprint(auth)

# Register main routes
from flask import render_template

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Server error occurred. Please try again."), 500

# Register new feature blueprints
from routes.media_tools import media_tools
from routes.editor_tools import editor_tools
from routes.security_tools import security_tools
from routes.static_pages import static_pages

app.register_blueprint(media_tools)
app.register_blueprint(editor_tools)
app.register_blueprint(security_tools)
app.register_blueprint(static_pages)
