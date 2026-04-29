"""
實時監控 API 路由模組 — 快爆指標、停損狀態、實時數據

負責向前端提供實時監控數據（JSON 格式），支援 AJAX 輪詢
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import timedelta, datetime
from app.models import (
    db, User, UserSettings, Room, RoomRecord, 
    AlertHistory, OperationLog, BettingRecord
)

# 建立 Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


def login_required(f):
    """登入驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '請先登入'}), 401
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/monitor/status', methods=['GET'])
@login_required
def monitor_status():
    """
    實時監控 API
    
    返回使用者的實時數據，包括：
    - 目前餘額與虧損
    - 停損狀態
    - 出金進度
    - 最新的快爆警告
    - 推薦房間的實時勝率
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "current_balance": 9500.00,
                "current_loss": 500.00,
                "loss_ratio": 5.0,
                "stop_loss_triggered": false,
                "stop_loss_threshold": 500.00,
                "daily_target": 1000.00,
                "daily_progress": 250.00,
                "daily_progress_ratio": 25.0,
                "recent_alerts": [...],
                "room_status": [...]
            }
        }
    """
    user_id = session.get('user_id')
    
    try:
        # 查詢使用者
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': '使用者不存在'}), 404
        
        # 查詢使用者設定
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            return jsonify({'success': False, 'error': '使用者設定未初始化'}), 400
        
        # 計算虧損相關數據
        current_balance = float(user.current_balance)
        initial_balance = float(user.initial_balance)
        current_loss = initial_balance - current_balance
        loss_ratio = (current_loss / initial_balance * 100) if initial_balance > 0 else 0
        
        # 判斷是否觸發停損
        stop_loss_triggered = False
        stop_loss_threshold = None
        
        if settings.stop_loss_amount:
            stop_loss_threshold = float(settings.stop_loss_amount)
            if current_loss >= stop_loss_threshold:
                stop_loss_triggered = True
        elif settings.stop_loss_percentage:
            threshold_pct = float(settings.stop_loss_percentage)
            stop_loss_threshold = initial_balance * threshold_pct / 100
            if current_loss >= stop_loss_threshold:
                stop_loss_triggered = True
        
        # 計算每日出金進度
        daily_target = float(settings.daily_target)
        
        # 查詢今日的出金記錄（示例：暫時為 0，可擴展為計算今日累計盈利）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = BettingRecord.query.filter(
            BettingRecord.user_id == user_id,
            BettingRecord.created_at >= today_start
        ).all()
        
        daily_profit = sum(float(r.profit or 0) for r in today_records)
        daily_progress_ratio = (daily_profit / daily_target * 100) if daily_target > 0 else 0
        
        # 查詢最新的 3 筆警告
        recent_alerts = AlertHistory.query.filter_by(user_id=user_id).order_by(
            AlertHistory.created_at.desc()
        ).limit(3).all()
        
        alerts_data = [
            {
                'id': alert.id,
                'type': alert.alert_type,
                'message': alert.alert_message,
                'burst_score': float(alert.burst_score) if alert.burst_score else None,
                'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': alert.is_read
            }
            for alert in recent_alerts
        ]
        
        # 查詢所有房間的實時勝率
        rooms = Room.query.filter_by(is_active=True).all()
        room_status = [
            {
                'id': room.id,
                'room_code': room.room_code,
                'room_name': room.room_name,
                'current_odds': float(room.current_odds),
                'win_rate': float(room.win_rate),
                'total_records': room.total_records,
                'last_updated': room.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            }
            for room in rooms
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'current_balance': round(current_balance, 2),
                'current_loss': round(current_loss, 2),
                'loss_ratio': round(loss_ratio, 2),
                'stop_loss_triggered': stop_loss_triggered,
                'stop_loss_threshold': round(stop_loss_threshold, 2) if stop_loss_threshold else None,
                'daily_target': round(daily_target, 2),
                'daily_progress': round(daily_profit, 2),
                'daily_progress_ratio': round(daily_progress_ratio, 2),
                'recent_alerts': alerts_data,
                'room_status': room_status
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'查詢監控數據失敗: {str(e)}'}), 500


@api_bp.route('/mark-alert-read', methods=['POST'])
@login_required
def mark_alert_read():
    """
    標記警告為已讀
    
    期望的 JSON 參數：
    {
        "alert_id": 123
    }
    
    Returns:
        JSON: { success: bool, message: str }
    """
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return jsonify({'success': False, 'error': '警告 ID 不能為空'}), 400
        
        # 查詢警告
        alert = AlertHistory.query.filter_by(id=alert_id, user_id=user_id).first()
        if not alert:
            return jsonify({'success': False, 'error': '警告不存在'}), 404
        
        # 標記為已讀
        alert.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': '已標記為讀取'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'標記失敗: {str(e)}'}), 500
