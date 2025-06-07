from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import re

auth = Blueprint('auth', __name__)

# Define a pattern for secure passwords
password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login requests.
    GET: Display login form.
    POST: Process login form submission.
    """
    # If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Find the user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        # Log in the user and remember them if requested
        login_user(user, remember=remember)
        
        # Redirect to the page they were trying to access or to the home page
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('index'))
        
    # GET request - show the login form
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration requests.
    GET: Display registration form.
    POST: Process registration form submission.
    """
    # If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Check if passwords match
        if password != password_confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check password strength
        if not password_pattern.match(password):
            flash('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if user with this email already exists
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            flash('Email address already in use.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if user with this username already exists
        user_name = User.query.filter_by(username=username).first()
        if user_name:
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new user
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        
        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        
        # Flash success message and redirect to login page
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    # GET request - show the registration form
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """
    Handle user logout requests.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth.route('/profile')
@login_required
def profile():
    """
    Display user profile page.
    """
    # Get user's file operations
    operations = current_user.operations.order_by(db.desc('created_at')).limit(10).all()
    return render_template('auth/profile.html', user=current_user, operations=operations)

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Handle user profile edit requests.
    GET: Display profile edit form.
    POST: Process profile edit form submission.
    """
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        
        # Check if username is already taken by another user
        user = User.query.filter_by(username=username).first()
        if user and user.id != current_user.id:
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.edit_profile'))
            
        # Update user details
        current_user.username = username
        db.session.commit()
        
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
        
    # GET request - show the profile edit form
    return render_template('auth/edit_profile.html', user=current_user)