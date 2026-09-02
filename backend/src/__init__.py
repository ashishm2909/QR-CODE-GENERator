from flask import Flask
from config import config
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import logging
import sqlite3
from whitenoise import WhiteNoise

from src.models import db, User

from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

migrate = Migrate()
csrf = CSRFProtect()


def _check_db_schema(app):
    """Check if SQLite database has the correct schema. Drop and recreate if outdated."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri.startswith('sqlite:///'):
        return  # Only handle SQLite

    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.exists(db_path):
        return  # No database yet, create_all will handle it

    # Check if database is writable — if not, delete and recreate
    if not os.access(db_path, os.W_OK):
        app.logger.warning("Database is read-only — removing and recreating")
        os.remove(db_path)
        return

    # Check if parent directory is writable
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.access(db_dir, os.W_OK):
        app.logger.error("Database directory is not writable: %s", db_dir)
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if users table has the subscription_status column
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {'subscription_status', 'plan_expires_at'}
        if not required_columns.issubset(columns):
            conn.close()
            app.logger.warning("Database schema outdated — recreating all tables")
            os.remove(db_path)
            return

        # Check if payments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        if not cursor.fetchone():
            conn.close()
            app.logger.warning("Payments table missing — recreating all tables")
            os.remove(db_path)
            return

        conn.close()
    except Exception as e:
        app.logger.warning("Error checking database schema: %s — recreating", e)
        if os.path.exists(db_path):
            os.remove(db_path)


def create_app(config_name='default'):
    # Determine template and static folders relative to this file
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(app_dir, '../frontend/templates')
    static_dir = os.path.join(app_dir, '../frontend/static')
    
    app = Flask(__name__, 
                template_folder=template_dir, 
                static_folder=static_dir)
    
    app.config.from_object(config[config_name])
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Apply Talisman security headers in production
    if config_name == 'production':
        Talisman(app,
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://checkout.razorpay.com",
                'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
                'font-src': "'self' https://fonts.gstatic.com",
                'img-src': "'self' data: https:",
                'frame-src': "https://api.razorpay.com",
            },
            force_https=False,
            strict_transport_security=True,
            referrer_policy='strict-origin-when-cross-origin',
        )
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix='static/')
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # For production, we prefer migrations. For development, auto-create tables.
    if config_name == 'development':
        with app.app_context():
            _check_db_schema(app)
            db.create_all()
            # Ensure database file is writable
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    os.chmod(db_path, 0o666)
    
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.main_routes import main_bp
    from .routes.api_routes import api_bp
    from .routes.payment_routes import payment_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)

    # Make Razorpay key available in all templates
    @app.context_processor
    def inject_payment_config():
        return {
            'razorpay_key_id': app.config.get('RAZORPAY_KEY_ID', ''),
        }
    
    return app
