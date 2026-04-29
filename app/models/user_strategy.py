"""
UserStrategy Model — 使用者下注策略

儲存使用者定義的下注策略（馬丁格爾、固定倍率、1-3-2-6 等）
"""

from datetime import datetime
from app.models import db


class UserStrategy(db.Model):
    """使用者下注策略模型"""
    
    __tablename__ = 'user_strategy'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # 策略資訊
    strategy_name = db.Column(db.String(100), nullable=False)
    strategy_type = db.Column(db.String(50), nullable=False)  # 'fixed', 'martingale', '1-3-2-6', 'custom'
    base_amount = db.Column(db.Numeric(10, 2), nullable=False)
    max_loss_streak = db.Column(db.Integer, nullable=False, default=5)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 狀態
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    
    # 關聯
    betting_records = db.relationship('BettingRecord', backref='strategy', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserStrategy {self.strategy_name} ({self.strategy_type})>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, user_id, strategy_name, strategy_type, base_amount, max_loss_streak=5):
        """
        新增下注策略
        
        Args:
            user_id (int): 使用者 ID
            strategy_name (str): 策略名稱
            strategy_type (str): 策略類型
            base_amount (Decimal): 基礎下注金額
            max_loss_streak (int, optional): 最大連敗上限
        
        Returns:
            UserStrategy: 新建立的策略物件
        """
        strategy = cls(
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            base_amount=base_amount,
            max_loss_streak=max_loss_streak
        )
        db.session.add(strategy)
        db.session.commit()
        return strategy
    
    @classmethod
    def get_by_id(cls, strategy_id):
        """
        根據 ID 查詢策略
        
        Args:
            strategy_id (int): 策略 ID
        
        Returns:
            UserStrategy: 策略物件或 None
        """
        return cls.query.get(strategy_id)
    
    @classmethod
    def get_by_user(cls, user_id, active_only=False):
        """
        查詢使用者的所有策略
        
        Args:
            user_id (int): 使用者 ID
            active_only (bool): 只查詢啟用策略
        
        Returns:
            list: 策略物件列表
        """
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def get_active_strategy(cls, user_id):
        """
        取得使用者目前啟用的策略
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            UserStrategy: 啟用的策略物件或 None
        """
        return cls.query.filter_by(user_id=user_id, is_active=True).first()
    
    def update(self, **kwargs):
        """
        更新策略
        
        Args:
            **kwargs: 要更新的欄位
        """
        allowed_fields = {'strategy_name', 'base_amount', 'max_loss_streak', 'is_active'}
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
    
    def delete(self):
        """刪除策略"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    def activate(self):
        """啟用此策略，並停用其他策略"""
        # 停用同一使用者的所有其他策略
        other_strategies = UserStrategy.query.filter(
            UserStrategy.user_id == self.user_id,
            UserStrategy.id != self.id
        ).all()
        for strategy in other_strategies:
            strategy.is_active = False
        
        self.is_active = True
        db.session.commit()
    
    def calculate_next_bet(self, current_loss_streak):
        """
        根據策略類型計算下一次下注金額
        
        Args:
            current_loss_streak (int): 目前連敗數
        
        Returns:
            Decimal: 建議的下注金額
        """
        base = float(self.base_amount)
        
        if self.strategy_type == 'fixed':
            # 固定下注
            return base
        
        elif self.strategy_type == 'martingale':
            # 馬丁格爾：每次加倍
            return base * (2 ** current_loss_streak)
        
        elif self.strategy_type == '1-3-2-6':
            # 1-3-2-6 系統
            sequence = [1, 3, 2, 6]
            bet_multiplier = sequence[current_loss_streak % len(sequence)]
            return base * bet_multiplier
        
        else:
            # 自訂或未知類型，回傳基礎金額
            return base
    
    def is_max_loss_streak_exceeded(self, current_loss_streak):
        """
        檢查是否超過最大連敗限制
        
        Args:
            current_loss_streak (int): 目前連敗數
        
        Returns:
            bool: 是否超過限制
        """
        return current_loss_streak >= self.max_loss_streak
    
    def get_strategy_description(self):
        """
        取得策略的中文描述
        
        Returns:
            str: 策略描述
        """
        descriptions = {
            'fixed': '固定下注：每局下注相同金額',
            'martingale': '馬丁格爾：連敗時下注金額翻倍',
            '1-3-2-6': '1-3-2-6 系統：按比例調整下注金額',
            'custom': '自訂策略'
        }
        return descriptions.get(self.strategy_type, '未知策略')
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type,
            'base_amount': float(self.base_amount),
            'max_loss_streak': self.max_loss_streak,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'description': self.get_strategy_description(),
        }
