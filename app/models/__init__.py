"""
Flask-SQLAlchemy 初始化模組

提供資料庫連線、ORM 實體映射與初始化邏輯
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 初始化 SQLAlchemy 實例
db = SQLAlchemy()


def init_db(app):
    """
    初始化資料庫
    
    Args:
        app: Flask 應用實例
    """
    db.init_app(app)
    
    with app.app_context():
        # 自動建立所有資料表
        db.create_all()


# 導入所有 Model 類別，讓 Flask 發現它們
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.room import Room
from app.models.room_record import RoomRecord
from app.models.user_strategy import UserStrategy
from app.models.betting_record import BettingRecord
from app.models.operation_log import OperationLog
from app.models.alert_history import AlertHistory

__all__ = [
    'db',
    'User',
    'UserSettings',
    'Room',
    'RoomRecord',
    'UserStrategy',
    'BettingRecord',
    'OperationLog',
    'AlertHistory',
]
