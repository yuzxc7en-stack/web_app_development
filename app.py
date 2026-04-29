"""
Flask 應用入口點

執行此文件以啟動開發伺服器
"""

import os
from app import create_app, db

# 建立應用實例
app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """
    Flask Shell 上下文
    
    允許在 `flask shell` 中直接訪問模型與資料庫
    """
    from app.models import (
        User, UserSettings, Room, RoomRecord,
        UserStrategy, BettingRecord, OperationLog, AlertHistory
    )
    
    return {
        'db': db,
        'User': User,
        'UserSettings': UserSettings,
        'Room': Room,
        'RoomRecord': RoomRecord,
        'UserStrategy': UserStrategy,
        'BettingRecord': BettingRecord,
        'OperationLog': OperationLog,
        'AlertHistory': AlertHistory,
    }


if __name__ == '__main__':
    # 初始化資料庫
    with app.app_context():
        db.create_all()
        print("✅ 資料庫初始化完成")
        print("📊 開發伺服器啟動: http://127.0.0.1:5000")
    
    # 啟動開發伺服器
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        use_reloader=True
    )
