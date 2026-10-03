"""
app/__init__.py — Application Factory
=======================================
Flask application factory pattern for Noise E-Commerce Site.
Initializes SQLAlchemy and registers blueprints dynamically.
"""
import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_name: str = 'development') -> Flask:
    """
    Application factory pattern for Noise E-Commerce Site.
    """
    app = Flask(__name__)

    # Import config
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    from config import config
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure instance directory exists
    os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints dynamically as phases are added
    try:
        from app.storefront import storefront as storefront_blueprint
        app.register_blueprint(storefront_blueprint, url_prefix='/')
    except (ImportError, AttributeError):
        pass

    try:
        from app.admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
    except (ImportError, AttributeError):
        pass

    # Register Global Template Helpers / Context Processors
    @app.context_processor
    def inject_global_data():
        cart_count = 0
        cart_total = 0.0
        sid = session.get('session_id')
        if sid:
            from app.models import CartItem
            try:
                items = CartItem.query.filter_by(session_id=sid).all()
                cart_count = sum(item.quantity for item in items)
                cart_total = sum(item.subtotal for item in items)
            except Exception:
                cart_count = 0
                cart_total = 0.0

        return {
            'cart_count': cart_count,
            'cart_total': cart_total,
            'currency': app.config.get('CURRENCY_SYMBOL', '₹'),
            'engine_url': app.config.get('RANKING_ENGINE_URL', 'http://localhost:5000')
        }

    # Create tables within app context
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
