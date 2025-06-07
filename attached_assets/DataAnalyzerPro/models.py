from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication and account management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to track user's file operations
    operations = db.relationship('FileOperation', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class FileOperation(db.Model):
    """Model to track file processing operations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    operation_type = db.Column(db.String(50), nullable=False)  # e.g., 'pdf_merge', 'image_convert'
    
    # Input and output file information
    original_filename = db.Column(db.String(256))
    result_filename = db.Column(db.String(256))
    input_path = db.Column(db.String(512))  # Path to the input file (temporary)
    output_path = db.Column(db.String(512))  # Path to the output file (temporary)
    
    # Operation details
    parameters = db.Column(db.Text)  # JSON-encoded parameters used for the operation
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    error_message = db.Column(db.Text)  # Error message if operation failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<FileOperation {self.operation_type} ({self.status})>'

class ExcelCommand(db.Model):
    """Model to store AI-based Excel commands and their translations"""
    id = db.Column(db.Integer, primary_key=True)
    natural_language = db.Column(db.Text, nullable=False)  # The command in natural language
    command_type = db.Column(db.String(50), nullable=False)  # Type of command (filter, sort, etc.)
    python_code = db.Column(db.Text)  # The Python/pandas code to execute the command
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExcelCommand {self.command_type}: {self.natural_language[:30]}>'