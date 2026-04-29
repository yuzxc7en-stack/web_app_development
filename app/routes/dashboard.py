"""
主控台路由模組 — 儀表板、日誌查詢、統計分析

負責顯示使用者的主控台頁面、操作日誌、警告記錄
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps
from app.models import (
    User, UserSettings, Room, OperationLog, 
    AlertHistory, RoomRecord, db
)

# 建立 Blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


def login_required(f):
    """
    登入驗證裝飾器
    
    檢查 Session 中是否有 user_id，若無則導向登入頁
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/', methods=['GET'])
@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    主控台首頁
    
    顯示：
    - 使用者的風控設定（停損、出金目標）
    - 推薦房間列表
    - 實時勝率與快爆指標
    """
    user_id = session.get('user_id')
    
    try:
        # 查詢使用者資訊
        user = User.get_by_id(user_id)
        if not user:
            flash('使用者不存在', 'error')
            session.clear()
            return redirect(url_for('auth.login'))
        
        # 查詢使用者設定
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            flash('使用者設定未初始化', 'error')
            return redirect(url_for('auth.login'))
        
        # 查詢所有房間（展示推薦清單）
        rooms = Room.query.filter_by(is_active=True).all()
        
        # 計算目前虧損與距離停損還有多少
        current_loss = float(user.initial_balance) - float(user.current_balance)
        stop_loss_threshold = None
        
        if settings.stop_loss_amount:
            stop_loss_threshold = float(settings.stop_loss_amount)
        elif settings.stop_loss_percentage:
            stop_loss_threshold = float(user.initial_balance) * float(settings.stop_loss_percentage) / 100
        
        loss_ratio = (current_loss / float(user.initial_balance) * 100) if user.initial_balance > 0 else 0
        
        # 查詢最新的警告（前 5 筆）
        recent_alerts = AlertHistory.query.filter_by(user_id=user_id).order_by(
            AlertHistory.created_at.desc()
        ).limit(5).all()
        
        return render_template(
            'index.html',
            user=user,
            settings=settings,
            rooms=rooms,
            current_loss=current_loss,
            loss_ratio=round(loss_ratio, 2),
            stop_loss_threshold=stop_loss_threshold,
            recent_alerts=recent_alerts
        )
    
    except Exception as e:
        flash(f'載入主控台時發生錯誤: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@dashboard_bp.route('/logs', methods=['GET'])
@login_required
def logs():
    """
    操作日誌頁面
    
    顯示：
    - 使用者的操作日誌（登入、登出、設定變更、停損觸發等）
    - 警告記錄（快爆預警、出金提醒等）
    """
    user_id = session.get('user_id')
    
    try:
        # 查詢使用者
        user = User.get_by_id(user_id)
        if not user:
            flash('使用者不存在', 'error')
            session.clear()
            return redirect(url_for('auth.login'))
        
        # 查詢操作日誌（最新的前 100 筆）
        operation_logs = OperationLog.query.filter_by(user_id=user_id).order_by(
            OperationLog.created_at.desc()
        ).limit(100).all()
        
        # 查詢警告記錄（最新的前 100 筆）
        alert_logs = AlertHistory.query.filter_by(user_id=user_id).order_by(
            AlertHistory.created_at.desc()
        ).limit(100).all()
        
        return render_template(
            'logs.html',
            user=user,
            operation_logs=operation_logs,
            alert_logs=alert_logs
        )
    
    except Exception as e:
        flash(f'載入日誌時發生錯誤: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard'))
