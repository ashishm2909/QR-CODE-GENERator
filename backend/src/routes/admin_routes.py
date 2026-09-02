from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from ..models import db, User, QRCode
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('admin.admin_login'))

        if not user.is_admin:
            flash('This account does not have admin access.', 'error')
            return redirect(url_for('admin.admin_login'))

        login_user(user)
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    qr_stats = {
        'total': QRCode.query.count(),
        'artistic': QRCode.query.filter_by(is_artistic=True).count(),
        'standard': QRCode.query.filter_by(is_artistic=False).count()
    }
    return render_template('admin/dashboard.html', users=users, qr_stats=qr_stats)

@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot change your own admin status'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'success': True, 'is_admin': user.is_admin})

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot delete yourself'}), 400
    
    # Delete associated QR codes first (due to foreign key)
    QRCode.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/update-plan/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_plan(user_id):
    user = User.query.get_or_404(user_id)
    new_plan = request.json.get('plan')
    if new_plan in ['free', 'pro', 'business']:
        user.plan = new_plan
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid plan'}), 400
