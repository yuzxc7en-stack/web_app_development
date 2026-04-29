"""
UserSettings Model — 使用者風控設定

儲存每位使用者的停損、出金目標、自動操作等風控參數
"""

from datetime import datetime
from app.models import db


class UserSettings(db.Model):
    """使用者風控設定模型"""
    
    __tablename__ = 'user_settings'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # 出金目標設定
    daily_target = db.Column(db.Numeric(12, 2), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)  # 'amount' 或 'percentage'
    
    # 停損設定
    stop_loss_amount = db.Column(db.Numeric(12, 2))  # 絕對金額停損
    stop_loss_percentage = db.Column(db.Numeric(5, 2))  # 百分比停損
    
    # 冷靜期設定
    cooldown_minutes = db.Column(db.Integer, nullable=False, default=30)
    
    # 自動操作
    auto_play_enabled = db.Column(db.Boolean, nullable=False, default=False)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, user_id, daily_target, target_type, stop_loss_amount=None, stop_loss_percentage=None):
        """
        新增使用者設定
        
        Args:
            user_id (int): 使用者 ID
            daily_target (Decimal): 每日出金目標
            target_type (str): 目標類型 ('amount' 或 'percentage')
            stop_loss_amount (Decimal, optional): 停損金額
            stop_loss_percentage (Decimal, optional): 停損百分比
        
        Returns:
            UserSettings: 新建立的設定物件
        """
        settings = cls(
            user_id=user_id,
            daily_target=daily_target,
            target_type=target_type,
            stop_loss_amount=stop_loss_amount,
            stop_loss_percentage=stop_loss_percentage
        )
        db.session.add(settings)
        db.session.commit()
        return settings
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """
        根據使用者 ID 查詢設定
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            UserSettings: 設定物件或 None
        """
        return cls.query.filter_by(user_id=user_id).first()
    
    def update(self, **kwargs):
        """
        更新設定
        
        Args:
            **kwargs: 要更新的欄位
        """
        allowed_fields = {
            'daily_target', 'target_type', 'stop_loss_amount', 
            'stop_loss_percentage', 'cooldown_minutes', 'auto_play_enabled'
        }
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def delete(self):
        """刪除設定"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    def is_stop_loss_triggered(self, user):
        """
        檢查是否觸發停損條件
        
        Args:
            user (User): 使用者物件
        
        Returns:
            bool: 是否觸發停損
        """
        current_loss, loss_percentage = user.get_current_loss()
        
        # 檢查絕對金額停損
        if self.stop_loss_amount and current_loss >= float(self.stop_loss_amount):
            return True
        
        # 檢查百分比停損
        if self.stop_loss_percentage and loss_percentage >= float(self.stop_loss_percentage):
            return True
        
        return False
    
    def is_daily_target_reached(self, user):
        """
        檢查是否達到每日出金目標
        
        Args:
            user (User): 使用者物件
        
        Returns:
            bool: 是否達到目標
        """
        current_profit, profit_percentage = user.get_current_profit()
        
        if self.target_type == 'amount':
            return current_profit >= float(self.daily_target)
        elif self.target_type == 'percentage':
            return profit_percentage >= float(self.daily_target)
        
        return False
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'daily_target': float(self.daily_target),
            'target_type': self.target_type,
            'stop_loss_amount': float(self.stop_loss_amount) if self.stop_loss_amount else None,
            'stop_loss_percentage': float(self.stop_loss_percentage) if self.stop_loss_percentage else None,
            'cooldown_minutes': self.cooldown_minutes,
            'auto_play_enabled': self.auto_play_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
