"""
AlertHistory Model — 警告記錄

記錄系統推送給使用者的所有快爆警告、風控提示與系統消息
"""

from datetime import datetime
from app.models import db


class AlertHistory(db.Model):
    """警告記錄模型"""
    
    __tablename__ = 'alert_history'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    
    # 警告資訊
    alert_type = db.Column(db.String(50), nullable=False)  # 'burst_warning', 'daily_target_reached', 'stop_loss_triggered', 'system_message'
    alert_message = db.Column(db.Text, nullable=False)
    
    # 快爆評分（僅用於快爆警告）
    burst_score = db.Column(db.Numeric(5, 2))  # 0-100，越高風險越大
    
    # 讀取狀態
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AlertHistory user_id={self.user_id} type={self.alert_type}>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, user_id, room_id, alert_type, alert_message, burst_score=None):
        """
        新增警告記錄
        
        Args:
            user_id (int): 使用者 ID
            room_id (int): 房間 ID
            alert_type (str): 警告類型
            alert_message (str): 警告訊息
            burst_score (Decimal, optional): 快爆評分（僅快爆警告）
        
        Returns:
            AlertHistory: 新建立的警告物件
        """
        alert = cls(
            user_id=user_id,
            room_id=room_id,
            alert_type=alert_type,
            alert_message=alert_message,
            burst_score=burst_score
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    
    @classmethod
    def get_by_id(cls, alert_id):
        """
        根據 ID 查詢警告
        
        Args:
            alert_id (int): 警告 ID
        
        Returns:
            AlertHistory: 警告物件或 None
        """
        return cls.query.get(alert_id)
    
    @classmethod
    def get_by_user(cls, user_id, limit=None, unread_only=False, order_desc=True):
        """
        查詢使用者的警告記錄
        
        Args:
            user_id (int): 使用者 ID
            limit (int, optional): 限制筆數
            unread_only (bool): 只查詢未讀警告
            order_desc (bool): 是否按時間從新到舊排序
        
        Returns:
            list: 警告物件列表
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        if order_desc:
            query = query.order_by(cls.created_at.desc())
        else:
            query = query.order_by(cls.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """
        計算使用者的未讀警告數
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            int: 未讀警告數
        """
        return cls.query.filter_by(user_id=user_id, is_read=False).count()
    
    @classmethod
    def get_by_type(cls, user_id, alert_type, limit=None):
        """
        查詢特定類型的警告
        
        Args:
            user_id (int): 使用者 ID
            alert_type (str): 警告類型
            limit (int, optional): 限制筆數
        
        Returns:
            list: 警告物件列表
        """
        query = cls.query.filter_by(user_id=user_id, alert_type=alert_type)
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent_burst_alerts(cls, user_id, hours=1):
        """
        查詢最近 N 小時內的快爆警告
        
        Args:
            user_id (int): 使用者 ID
            hours (int): 小時數
        
        Returns:
            list: 快爆警告物件列表
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return cls.query.filter(
            cls.user_id == user_id,
            cls.alert_type == 'burst_warning',
            cls.created_at >= cutoff_time
        ).order_by(cls.created_at.desc()).all()
    
    def mark_as_read(self):
        """標記警告為已讀"""
        self.is_read = True
        db.session.commit()
    
    def delete(self):
        """刪除警告"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    def get_alert_severity(self):
        """
        判斷警告的嚴重程度（基於類型與分數）
        
        Returns:
            str: 'critical', 'high', 'medium', 'low'
        """
        if self.alert_type == 'stop_loss_triggered':
            return 'critical'
        elif self.alert_type == 'daily_target_reached':
            return 'high'
        elif self.alert_type == 'burst_warning':
            if self.burst_score and float(self.burst_score) >= 80:
                return 'critical'
            elif self.burst_score and float(self.burst_score) >= 60:
                return 'high'
            elif self.burst_score and float(self.burst_score) >= 40:
                return 'medium'
            else:
                return 'low'
        else:
            return 'low'
    
    @classmethod
    def log_burst_warning(cls, user_id, room_id, burst_score, room_name):
        """
        記錄快爆警告
        
        Args:
            user_id (int): 使用者 ID
            room_id (int): 房間 ID
            burst_score (Decimal): 快爆評分
            room_name (str): 房間名稱
        """
        message = f'🚨 快爆預警：房間 {room_name} 偵測到快爆風險（分數：{burst_score}），請注意風險！'
        return cls.create(
            user_id=user_id,
            room_id=room_id,
            alert_type='burst_warning',
            alert_message=message,
            burst_score=burst_score
        )
    
    @classmethod
    def log_daily_target_reached(cls, user_id, room_id, target_amount):
        """
        記錄達成每日目標警告
        
        Args:
            user_id (int): 使用者 ID
            room_id (int): 房間 ID
            target_amount (Decimal): 目標金額
        """
        message = f'✅ 恭喜！您已達成今日出金目標（{target_amount}），建議立即出金，避免貪婪造成損失。'
        return cls.create(
            user_id=user_id,
            room_id=room_id,
            alert_type='daily_target_reached',
            alert_message=message
        )
    
    @classmethod
    def log_stop_loss_triggered(cls, user_id, room_id, loss_amount):
        """
        記錄停損觸發警告
        
        Args:
            user_id (int): 使用者 ID
            room_id (int): 房間 ID
            loss_amount (Decimal): 虧損金額
        """
        message = f'🛑 緊急停損：您的虧損已達設定閥值（{loss_amount}），系統已自動暫停所有操作，請冷靜思考。'
        return cls.create(
            user_id=user_id,
            room_id=room_id,
            alert_type='stop_loss_triggered',
            alert_message=message
        )
    
    @classmethod
    def log_system_message(cls, user_id, room_id, message):
        """
        記錄系統消息
        
        Args:
            user_id (int): 使用者 ID
            room_id (int): 房間 ID
            message (str): 系統消息內容
        """
        return cls.create(
            user_id=user_id,
            room_id=room_id,
            alert_type='system_message',
            alert_message=message
        )
    
    @classmethod
    def get_alert_dashboard(cls, user_id, limit=10):
        """
        取得警告看板資訊（用於主控台顯示）
        
        Args:
            user_id (int): 使用者 ID
            limit (int): 取得最近 N 筆
        
        Returns:
            dict: 警告看板資訊
        """
        all_alerts = cls.get_by_user(user_id, limit=limit, order_desc=True)
        unread_count = cls.get_unread_count(user_id)
        
        # 統計各類型警告
        type_counts = {}
        for alert_type in ['burst_warning', 'daily_target_reached', 'stop_loss_triggered', 'system_message']:
            type_counts[alert_type] = cls.query.filter_by(user_id=user_id, alert_type=alert_type).count()
        
        return {
            'unread_count': unread_count,
            'recent_alerts': [alert.to_dict() for alert in all_alerts],
            'type_counts': type_counts,
            'critical_alerts': [
                alert.to_dict() for alert in all_alerts 
                if alert.get_alert_severity() in ['critical', 'high']
            ]
        }
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'alert_type': self.alert_type,
            'alert_message': self.alert_message,
            'burst_score': float(self.burst_score) if self.burst_score else None,
            'is_read': self.is_read,
            'severity': self.get_alert_severity(),
            'created_at': self.created_at.isoformat(),
        }
