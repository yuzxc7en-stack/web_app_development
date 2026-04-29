"""
策略設定路由模組 — 風控設定更新、停損/出金配置

負責接收並驗證使用者的風控參數變更
"""

from flask import Blueprint, request, jsonify, session, flash, redirect, url_for
from functools import wraps
from app.models import db, User, UserSettings, OperationLog

# 建立 Blueprint
strategy_bp = Blueprint('strategy', __name__, url_prefix='/api')


def login_required(f):
    """登入驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '請先登入'}), 401
        return f(*args, **kwargs)
    return decorated_function


@strategy_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    """
    更新使用者的風控設定
    
    期望的 JSON 參數：
    {
        "daily_target": 1000,           # 每日出金目標
        "target_type": "amount",        # 目標類型 ('amount' 或 'percentage')
        "stop_loss_amount": 500,        # 停損金額（可選）
        "stop_loss_percentage": 10,     # 停損百分比（可選）
        "auto_play_enabled": false      # 自動操作開關（可選）
    }
    
    Returns:
        JSON: { success: bool, message: str, data: { ... } }
    """
    user_id = session.get('user_id')
    
    try:
        # 驗證使用者是否存在
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': '使用者不存在'}), 404
        
        # 取得 JSON 數據
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '無效的請求格式'}), 400
        
        # 輸入驗證
        daily_target = data.get('daily_target')
        target_type = data.get('target_type', 'amount')
        stop_loss_amount = data.get('stop_loss_amount')
        stop_loss_percentage = data.get('stop_loss_percentage')
        auto_play_enabled = data.get('auto_play_enabled', False)
        
        # 驗證必填欄位
        if daily_target is None:
            return jsonify({'success': False, 'error': '每日出金目標不能為空'}), 400
        
        if target_type not in ['amount', 'percentage']:
            return jsonify({'success': False, 'error': '無效的目標類型'}), 400
        
        # 驗證數值有效性
        try:
            daily_target = float(daily_target)
            if daily_target <= 0:
                raise ValueError('必須為正數')
            
            if stop_loss_amount is not None:
                stop_loss_amount = float(stop_loss_amount)
                if stop_loss_amount < 0:
                    raise ValueError('停損金額不能為負數')
            
            if stop_loss_percentage is not None:
                stop_loss_percentage = float(stop_loss_percentage)
                if not 0 <= stop_loss_percentage <= 100:
                    raise ValueError('停損百分比必須在 0-100 之間')
        
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'數值驗證失敗: {str(e)}'}), 400
        
        # 查詢或建立使用者設定
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        
        if settings:
            # 更新現有設定
            settings.daily_target = daily_target
            settings.target_type = target_type
            settings.stop_loss_amount = stop_loss_amount
            settings.stop_loss_percentage = stop_loss_percentage
            settings.auto_play_enabled = auto_play_enabled
        else:
            # 建立新設定
            settings = UserSettings.create(
                user_id=user_id,
                daily_target=daily_target,
                target_type=target_type,
                stop_loss_amount=stop_loss_amount,
                stop_loss_percentage=stop_loss_percentage
            )
            settings.auto_play_enabled = auto_play_enabled
        
        db.session.commit()
        
        # 記錄操作日誌
        OperationLog.create(
            user_id=user_id,
            operation_type='settings_updated',
            status='success',
            reason='使用者更新風控設定',
            details={
                'daily_target': float(daily_target),
                'target_type': target_type,
                'stop_loss_amount': float(stop_loss_amount) if stop_loss_amount else None,
                'stop_loss_percentage': float(stop_loss_percentage) if stop_loss_percentage else None,
                'auto_play_enabled': auto_play_enabled
            }
        )
        
        return jsonify({
            'success': True,
            'message': '設定更新成功',
            'data': {
                'daily_target': float(daily_target),
                'target_type': target_type,
                'stop_loss_amount': float(stop_loss_amount) if stop_loss_amount else None,
                'stop_loss_percentage': float(stop_loss_percentage) if stop_loss_percentage else None,
                'auto_play_enabled': auto_play_enabled
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'設定更新失敗: {str(e)}'}), 500
