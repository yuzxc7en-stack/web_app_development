"""
OperationLog Model — 操作日誌

記錄所有系統關鍵操作（登入、登出、停損觸發、出金、設定變更等）
採用 Append-Only 設計，不允許修改或刪除過去的紀錄
"""

from datetime import datetime
from app.models import db
import json


class OperationLog(db.Model):
    """操作日誌模型"""
    
    __tablename__ = 'operation_log'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 操作資訊
    operation_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'stop_loss_triggered', 等
    amount = db.Column(db.Numeric(12, 2))  # 涉及的金額
    status = db.Column(db.String(20), nullable=False, default='success')  # 'success', 'pending', 'failed'
    reason = db.Column(db.Text)  # 操作原因
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 詳細資訊（JSON 格式）
    details = db.Column(db.Text)  # 額外的 JSON 詳細資訊
    
    def __repr__(self):
        return f'<OperationLog user_id={self.user_id} type={self.operation_type}>'
    
    # ============ CREATE 方法 ============
    
    @classmethod
    def create(cls, user_id, operation_type, status='success', amount=None, reason=None, details=None):
        """
        新增操作日誌
        
        **注意**：此模型採用 Append-Only 設計，只允許新增，不允許修改或刪除
        
        Args:
            user_id (int): 使用者 ID
            operation_type (str): 操作類型
            status (str, optional): 狀態
            amount (Decimal, optional): 涉及的金額
            reason (str, optional): 操作原因
            details (dict, optional): 額外詳細資訊（會自動轉為 JSON）
        
        Returns:
            OperationLog: 新建立的日誌物件
        """
        log = cls(
            user_id=user_id,
            operation_type=operation_type,
            status=status,
            amount=amount,
            reason=reason,
            details=json.dumps(details) if details else None
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def get_by_id(cls, log_id):
        """
        根據 ID 查詢日誌
        
        Args:
            log_id (int): 日誌 ID
        
        Returns:
            OperationLog: 日誌物件或 None
        """
        return cls.query.get(log_id)
    
    @classmethod
    def get_by_user(cls, user_id, limit=None, operation_type=None, order_desc=True):
        """
        查詢使用者的操作日誌
        
        Args:
            user_id (int): 使用者 ID
            limit (int, optional): 限制筆數
            operation_type (str, optional): 篩選特定操作類型
            order_desc (bool): 是否按時間從新到舊排序
        
        Returns:
            list: 日誌物件列表
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if operation_type:
            query = query.filter_by(operation_type=operation_type)
        
        if order_desc:
            query = query.order_by(cls.created_at.desc())
        else:
            query = query.order_by(cls.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_recent_by_type(cls, user_id, operation_type, hours=24):
        """
        查詢最近 N 小時內特定類型的操作
        
        Args:
            user_id (int): 使用者 ID
            operation_type (str): 操作類型
            hours (int): 小時數
        
        Returns:
            list: 日誌物件列表
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return cls.query.filter(
            cls.user_id == user_id,
            cls.operation_type == operation_type,
            cls.created_at >= cutoff_time
        ).order_by(cls.created_at.desc()).all()
    
    # ============ 禁用修改與刪除 ============
    
    def update(self, **kwargs):
        """
        禁止修改操作日誌（Append-Only 原則）
        
        Raises:
            RuntimeError: 總是拋出此異常
        """
        raise RuntimeError('操作日誌不允許修改，這違反了 Append-Only 的審計原則')
    
    def delete(self):
        """
        禁止刪除操作日誌（Append-Only 原則）
        
        Raises:
            RuntimeError: 總是拋出此異常
        """
        raise RuntimeError('操作日誌不允許刪除，這違反了 Append-Only 的審計原則')
    
    # ============ 業務邏輯方法 ============
    
    def get_details_dict(self):
        """
        取得詳細資訊的 JSON 物件
        
        Returns:
            dict: 詳細資訊字典，若無則回傳空字典
        """
        if self.details:
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @classmethod
    def log_login(cls, user_id, ip_address=None):
        """記錄使用者登入"""
        return cls.create(
            user_id=user_id,
            operation_type='login',
            reason='使用者登入系統',
            details={'ip_address': ip_address} if ip_address else None
        )
    
    @classmethod
    def log_logout(cls, user_id):
        """記錄使用者登出"""
        return cls.create(
            user_id=user_id,
            operation_type='logout',
            reason='使用者登出系統'
        )
    
    @classmethod
    def log_stop_loss_triggered(cls, user_id, loss_amount, trigger_reason):
        """
        記錄停損觸發事件
        
        Args:
            user_id (int): 使用者 ID
            loss_amount (Decimal): 虧損金額
            trigger_reason (str): 觸發原因（'amount' 或 'percentage'）
        """
        return cls.create(
            user_id=user_id,
            operation_type='stop_loss_triggered',
            status='success',
            amount=loss_amount,
            reason=f'停損被觸發：{trigger_reason}',
            details={'trigger_reason': trigger_reason, 'loss_amount': float(loss_amount)}
        )
    
    @classmethod
    def log_withdrawal(cls, user_id, withdrawal_amount, target_reason):
        """
        記錄出金（達成每日目標）
        
        Args:
            user_id (int): 使用者 ID
            withdrawal_amount (Decimal): 出金金額
            target_reason (str): 達成目標原因
        """
        return cls.create(
            user_id=user_id,
            operation_type='withdrawal',
            status='success',
            amount=withdrawal_amount,
            reason=f'達成每日目標出金：{target_reason}'
        )
    
    @classmethod
    def log_settings_update(cls, user_id, updated_fields):
        """
        記錄使用者設定變更
        
        Args:
            user_id (int): 使用者 ID
            updated_fields (dict): 被更新的欄位
        """
        return cls.create(
            user_id=user_id,
            operation_type='settings_update',
            reason='使用者更新風控設定',
            details=updated_fields
        )
    
    @classmethod
    def log_auto_play_start(cls, user_id, strategy_name):
        """記錄自動操作啟動"""
        return cls.create(
            user_id=user_id,
            operation_type='auto_play_start',
            reason=f'啟動自動操作策略：{strategy_name}',
            details={'strategy_name': strategy_name}
        )
    
    @classmethod
    def log_auto_play_stop(cls, user_id, stop_reason):
        """記錄自動操作停止"""
        return cls.create(
            user_id=user_id,
            operation_type='auto_play_stop',
            reason=f'停止自動操作：{stop_reason}',
            details={'stop_reason': stop_reason}
        )
    
    @classmethod
    def get_daily_summary(cls, user_id, date_obj=None):
        """
        取得使用者的每日操作摘要
        
        Args:
            user_id (int): 使用者 ID
            date_obj (date, optional): 查詢日期，若無則以今日計
        
        Returns:
            dict: 操作摘要
        """
        from datetime import date
        if not date_obj:
            date_obj = date.today()
        
        daily_logs = cls.query.filter(
            cls.user_id == user_id,
            db.func.date(cls.created_at) == date_obj
        ).all()
        
        return {
            'date': date_obj.isoformat(),
            'total_operations': len(daily_logs),
            'login_count': sum(1 for log in daily_logs if log.operation_type == 'login'),
            'logout_count': sum(1 for log in daily_logs if log.operation_type == 'logout'),
            'stop_loss_count': sum(1 for log in daily_logs if log.operation_type == 'stop_loss_triggered'),
            'withdrawal_count': sum(1 for log in daily_logs if log.operation_type == 'withdrawal'),
            'logs': [log.to_dict() for log in daily_logs]
        }
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation_type': self.operation_type,
            'amount': float(self.amount) if self.amount else None,
            'status': self.status,
            'reason': self.reason,
            'details': self.get_details_dict(),
            'created_at': self.created_at.isoformat(),
        }
