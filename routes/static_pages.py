import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app

static_pages = Blueprint('static_pages', __name__)

@static_pages.route('/about')
def about():
    """Render the About Us page"""
    return render_template('pages/about.html')

@static_pages.route('/features')
def features():
    """Render the Features page"""
    return render_template('pages/features.html')

@static_pages.route('/pricing')
def pricing():
    """Render the Pricing page"""
    return render_template('pages/pricing.html')

@static_pages.route('/blog')
def blog():
    """Render the Blog page"""
    return render_template('pages/blog.html')

@static_pages.route('/faq')
def faq():
    """Render the FAQ page"""
    return render_template('pages/faq.html')

@static_pages.route('/privacy')
def privacy():
    """Render the Privacy Policy page"""
    return render_template('pages/privacy.html')

@static_pages.route('/support')
def support():
    """Render the Support page with AI chatbot"""
    return render_template('pages/support.html')