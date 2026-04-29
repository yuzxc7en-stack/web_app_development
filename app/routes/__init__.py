"""
路由初始化模組

導入並註冊所有 Blueprint
"""

from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.strategy import strategy_bp
from app.routes.api import api_bp


def register_blueprints(app):
    """
    註冊所有 Blueprint 到 Flask app
    
    Args:
        app: Flask 應用實例
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(api_bp)


__all__ = ['auth_bp', 'dashboard_bp', 'strategy_bp', 'api_bp', 'register_blueprints']
