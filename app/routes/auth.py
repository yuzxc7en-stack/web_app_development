"""
認證路由模組 — 登入、登出、會話管理

負責處理使用者認證、Session 管理、密碼驗證
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import db, User, OperationLog

# 建立 Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    登入路由
    
    GET: 顯示登入表單
    POST: 驗證登入、寫入 Session
    """
    if request.method == 'GET':
        # 如果已登入，自動導向至主控台
        if 'user_id' in session:
            return redirect(url_for('dashboard.dashboard'))
        return render_template('login.html')
    
    # POST 請求 — 驗證登入
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # 輸入驗證
    if not username or not password:
        flash('帳號和密碼不能為空', 'error')
        return render_template('login.html')
    
    try:
        # 查詢使用者
        user = User.get_by_username(username)
        if not user:
            flash('帳號或密碼錯誤', 'error')
            OperationLog.create(
                user_id=None,
                operation_type='login_failed',
                status='failed',
                reason=f'帳號不存在: {username}'
            )
            return render_template('login.html')
        
        # 驗證密碼
        if not check_password_hash(user.password_hash, password):
            flash('帳號或密碼錯誤', 'error')
            OperationLog.create(
                user_id=user.id,
                operation_type='login_failed',
                status='failed',
                reason='密碼錯誤'
            )
            return render_template('login.html')
        
        # 驗證帳號是否被停用
        if not user.is_active:
            flash('此帳號已被停用', 'error')
            return render_template('login.html')
        
        # 寫入 Session
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True
        
        # 記錄登入日誌
        OperationLog.create(
            user_id=user.id,
            operation_type='login',
            status='success'
        )
        
        flash('登入成功！', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    except Exception as e:
        flash(f'登入時發生錯誤: {str(e)}', 'error')
        return render_template('login.html')


@auth_bp.route('/logout', methods=['GET'])
def logout():
    """
    登出路由
    
    清除 Session、記錄登出日誌、導回登入頁
    """
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 記錄登出日誌
    if user_id:
        try:
            OperationLog.create(
                user_id=user_id,
                operation_type='logout',
                status='success'
            )
        except Exception as e:
            print(f'記錄登出日誌失敗: {str(e)}')
    
    # 清除 Session
    session.clear()
    flash('已登出系統', 'info')
    return redirect(url_for('auth.login'))
