"""
Flask 應用初始化模組

配置資料庫連線、初始化擴展、註冊藍圖等
"""

from flask import Flask
from app.models import db, init_db


def create_app(config_name='development'):
    """
    工廠函式：建立並配置 Flask 應用
    
    Args:
        config_name (str): 配置模式 ('development', 'testing', 'production')
    
    Returns:
        Flask: 已初始化的 Flask 應用實例
    """
    app = Flask(__name__)
    
    # ============ 資料庫配置 ============
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = (config_name == 'development')  # 開發環境顯示 SQL
    
    # ============ 會話配置 ============
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SESSION_COOKIE_SECURE'] = (config_name == 'production')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 小時
    
    # ============ 初始化資料庫 ============
    db.init_app(app)
    init_db(app)
    
    # ============ 導入模型（確保 SQLAlchemy 知道所有表） ============
    with app.app_context():
        from app.models import (
            User, UserSettings, Room, RoomRecord,
            UserStrategy, BettingRecord, OperationLog, AlertHistory
        )
    
    # ============ 註冊 Blueprint ============
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # ============ 健康檢查 ============
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康檢查端點"""
        return {
            'status': 'ok',
            'database': 'connected'
        }, 200
    
    return app


# ============ 開發環境快速啟動 ============
if __name__ == '__main__':
    app = create_app('development')
    
    # 在應用上下文中初始化資料庫
    with app.app_context():
        db.create_all()
        print("✅ 資料庫初始化完成")
    
    # 啟動開發伺服器
    app.run(debug=True, host='127.0.0.1', port=5000)
