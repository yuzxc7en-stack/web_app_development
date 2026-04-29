"""
初始化測試數據

此指令稿建立測試用戶及房間數據，用於整合測試
"""

import sys
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# 添加應用根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import (
    User, UserSettings, Room, RoomRecord, 
    AlertHistory, OperationLog, BettingRecord, UserStrategy
)


def init_test_data():
    """初始化測試數據"""
    
    app = create_app('development')
    
    with app.app_context():
        # 刪除所有表
        print("🗑️  清空資料庫...")
        db.drop_all()
        
        # 重建所有表
        print("📊 建立資料表...")
        db.create_all()
        
        # 建立測試用戶
        print("👤 建立測試用戶...")
        admin_user = User.create(
            username='admin',
            password_hash=generate_password_hash('password'),
            email='admin@example.com',
            initial_balance=10000
        )
        print(f"   ✅ 帳號: admin | 密碼: password | 本金: NT$ 10000")
        
        # 建立用戶設定
        print("⚙️  建立用戶設定...")
        settings = UserSettings.create(
            user_id=admin_user.id,
            daily_target=1000,
            target_type='amount',
            stop_loss_amount=500,
            stop_loss_percentage=None
        )
        print(f"   ✅ 每日目標: NT$ 1000 | 停損: NT$ 500")
        
        # 建立測試房間
        print("🎰 建立測試房間...")
        rooms_data = [
            ('A001', '龍虎遊戲1號房', 1.95, 52.3),
            ('A002', '龍虎遊戲2號房', 1.92, 48.7),
            ('A003', '骰寶1號房', 2.05, 55.2),
            ('B001', '百家樂豪華房', 1.98, 51.5),
            ('B002', '百家樂競技房', 1.99, 49.8),
        ]
        
        rooms = []
        for room_code, room_name, odds, win_rate in rooms_data:
            room = Room.create(
                room_code=room_code,
                room_name=room_name,
                current_odds=odds,
                win_rate=win_rate
            )
            rooms.append(room)
            print(f"   ✅ {room_code} - {room_name} (勝率: {win_rate}%)")
        
        # 建立歷史房間記錄
        print("📈 建立房間開獎記錄...")
        for i in range(20):
            for room in rooms:
                record = RoomRecord.create(
                    user_id=admin_user.id,
                    room_id=room.id,
                    result='win' if random.random() > 0.45 else 'lose',
                    odds=float(room.current_odds) + random.uniform(-0.1, 0.1)
                )
        print(f"   ✅ 建立 {len(rooms) * 20} 筆房間記錄")
        
        # 建立操作日誌
        print("📝 建立操作日誌...")
        log_types = [
            ('login', 'success'),
            ('settings_updated', 'success'),
            ('stop_loss_triggered', 'success'),
        ]
        
        for log_type, status in log_types:
            log = OperationLog.create(
                user_id=admin_user.id,
                operation_type=log_type,
                status=status,
                reason=f'測試日誌: {log_type}'
            )
        print(f"   ✅ 建立 {len(log_types)} 筆操作日誌")
        
        # 建立警告記錄
        print("🚨 建立警告記錄...")
        alert_types = [
            ('burst_warning', '快爆指標異常升高'),
            ('daily_target_reached', '已達到每日出金目標'),
            ('stop_loss_warning', '接近停損閾值'),
        ]
        
        for alert_type, message in alert_types:
            for room in rooms[:3]:
                alert = AlertHistory.create(
                    user_id=admin_user.id,
                    room_id=room.id,
                    alert_type=alert_type,
                    alert_message=message,
                    burst_score=random.uniform(30, 95) if alert_type == 'burst_warning' else None
                )
        print(f"   ✅ 建立 {len(alert_types) * 3} 筆警告記錄")
        
        print("\n" + "="*50)
        print("✅ 測試資料初始化完成！")
        print("="*50)
        print("\n📋 測試帳號信息:")
        print(f"   帳號: admin")
        print(f"   密碼: password")
        print(f"   本金: NT$ 10000")
        print(f"\n🚀 啟動伺服器：python app.py")
        print(f"📌 訪問地址：http://127.0.0.1:5000/login")
        print("="*50)


if __name__ == '__main__':
    init_test_data()
