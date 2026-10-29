import os
from flask import Flask, render_template
from app.config import Config
from app.database import db
from app.utils.auth_helpers import get_current_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global context processor
    @app.context_processor
    def inject_globals():
        return {
            'current_user': get_current_user(),
            'currency_symbol': app.config.get('CURRENCY_SYMBOL', '₹'),
            'cancellation_policy': app.config.get('CANCELLATION_POLICY_DESC')
        }

    # Template filters
    @app.template_filter('format_currency')
    def format_currency(val):
        sym = app.config.get('CURRENCY_SYMBOL', '₹')
        try:
            return f"{sym}{float(val):,.2f}"
        except (ValueError, TypeError):
            return f"{sym}0.00"

    @app.template_filter('format_date')
    def format_date(dt):
        if not dt:
            return ""
        if hasattr(dt, 'strftime'):
            return dt.strftime('%b %d, %Y')
        return str(dt)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app
