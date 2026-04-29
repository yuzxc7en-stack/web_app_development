"""
User Model — 使用者帳號與基本資訊

儲存登入帳號、密碼、餘額等使用者核心資訊
"""

from datetime import datetime
from app.models import db


class User(db.Model):
    """使用者模型"""
    
    __tablename__ = 'user'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 基本資訊
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    
    # 資金管理
    initial_balance = db.Column(db.Numeric(12, 2), nullable=False)
    current_balance = db.Column(db.Numeric(12, 2), nullable=False)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 狀態
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # 關聯
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    operation_logs = db.relationship('OperationLog', backref='user', cascade='all, delete-orphan')
    alerts = db.relationship('AlertHistory', backref='user', cascade='all, delete-orphan')
    betting_records = db.relationship('BettingRecord', backref='user', cascade='all, delete-orphan')
    strategies = db.relationship('UserStrategy', backref='user', cascade='all, delete-orphan')
    room_records = db.relationship('RoomRecord', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, username, password_hash, email, initial_balance):
        """
        新增使用者
        
        Args:
            username (str): 帳號名稱
            password_hash (str): 密碼雜湊值
            email (str): 電郵
            initial_balance (Decimal): 初始本金
        
        Returns:
            User: 新建立的使用者物件
        """
        user = cls(
            username=username,
            password_hash=password_hash,
            email=email,
            initial_balance=initial_balance,
            current_balance=initial_balance
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def get_by_id(cls, user_id):
        """
        根據 ID 查詢使用者
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            User: 使用者物件或 None
        """
        return cls.query.get(user_id)
    
    @classmethod
    def get_by_username(cls, username):
        """
        根據帳號名稱查詢使用者
        
        Args:
            username (str): 帳號名稱
        
        Returns:
            User: 使用者物件或 None
        """
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_all(cls, active_only=True):
        """
        查詢所有使用者
        
        Args:
            active_only (bool): 只查詢啟用帳號
        
        Returns:
            list: 使用者物件列表
        """
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    def update(self, **kwargs):
        """
        更新使用者資訊
        
        Args:
            **kwargs: 要更新的欄位（如 current_balance, email, is_active）
        """
        allowed_fields = {'current_balance', 'email', 'is_active', 'password_hash'}
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def delete(self):
        """刪除使用者"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    def update_balance(self, amount):
        """
        更新使用者餘額（支援正負數）
        
        Args:
            amount (Decimal): 要加或減的金額
        """
        self.current_balance = float(self.current_balance) + float(amount)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_current_loss(self):
        """
        計算目前虧損（相對於初始本金）
        
        Returns:
            tuple: (虧損金額, 虧損百分比)
        """
        loss_amount = float(self.initial_balance) - float(self.current_balance)
        loss_percentage = (loss_amount / float(self.initial_balance) * 100) if self.initial_balance else 0
        return loss_amount, loss_percentage
    
    def get_current_profit(self):
        """
        計算目前獲利（相對於初始本金）
        
        Returns:
            tuple: (獲利金額, 獲利百分比)
        """
        profit_amount = float(self.current_balance) - float(self.initial_balance)
        profit_percentage = (profit_amount / float(self.initial_balance) * 100) if self.initial_balance else 0
        return profit_amount, profit_percentage
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'initial_balance': float(self.initial_balance),
            'current_balance': float(self.current_balance),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
