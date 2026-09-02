from flask import Blueprint, render_template, request, make_response, redirect, url_for, send_from_directory, current_app, jsonify
from flask_login import login_required, current_user
from ..models import QRCode
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/generate-qr')
def generate_qr():
    return render_template('generator.html')

@main_bp.route('/artistic-studio')
def artistic_studio():
    return render_template('artistic.html')

@main_bp.route('/scanner')
def scanner():
    return render_template('scanner.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    qrs = QRCode.query.filter_by(user_id=current_user.id).order_by(QRCode.created_at.desc()).all()
    return render_template('dashboard.html', qrs=qrs)

@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/templates')
def templates():
    return render_template('templates.html')

@main_bp.route('/changelog')
def changelog():
    return render_template('changelog.html')

@main_bp.route('/docs')
def docs():
    return render_template('docs.html')

@main_bp.route('/guides')
def guides():
    return render_template('guides.html')

@main_bp.route('/blog')
def blog():
    return render_template('blog.html')

@main_bp.route('/support')
def support():
    return render_template('support.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/careers')
def careers():
    return render_template('careers.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/set-plan/<plan>')
@login_required
def set_plan(plan: str):
    """Update the current user's plan. Only allows 'free' downgrade; upgrades require admin."""
    if plan not in ('free', 'pro', 'business'):
        return redirect(url_for('main.pricing'))
    # Only allow users to downgrade to free. Upgrades must go through admin/payment.
    if plan == 'free' or current_user.is_admin:
        current_user.plan = plan
        from ..models import db
        db.session.commit()
    response = make_response(redirect(request.args.get('next') or url_for('main.pricing')))
    return response

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "qr-generator-backend"}), 200
