"""
Room Model — 遊戲房間

儲存可選遊戲房間的基本資訊與即時統計（勝率、賠率等）
"""

from datetime import datetime
from app.models import db


class Room(db.Model):
    """遊戲房間模型"""
    
    __tablename__ = 'room'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 房間資訊
    room_code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    room_name = db.Column(db.String(100), nullable=False)
    
    # 統計資訊
    current_odds = db.Column(db.Numeric(5, 2), nullable=False)
    total_records = db.Column(db.Integer, nullable=False, default=0)
    win_rate = db.Column(db.Numeric(5, 2), nullable=False, default=50.0)
    
    # 時間戳記
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 狀態
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # 關聯
    records = db.relationship('RoomRecord', backref='room', cascade='all, delete-orphan')
    alerts = db.relationship('AlertHistory', backref='room', cascade='all, delete-orphan')
    betting_records = db.relationship('BettingRecord', backref='room', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Room {self.room_code} ({self.room_name})>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, room_code, room_name, current_odds, win_rate=50.0):
        """
        新增房間
        
        Args:
            room_code (str): 房間代碼（如 A123）
            room_name (str): 房間名稱
            current_odds (Decimal): 目前賠率
            win_rate (Decimal, optional): 初始勝率
        
        Returns:
            Room: 新建立的房間物件
        """
        room = cls(
            room_code=room_code,
            room_name=room_name,
            current_odds=current_odds,
            win_rate=win_rate
        )
        db.session.add(room)
        db.session.commit()
        return room
    
    @classmethod
    def get_by_id(cls, room_id):
        """
        根據 ID 查詢房間
        
        Args:
            room_id (int): 房間 ID
        
        Returns:
            Room: 房間物件或 None
        """
        return cls.query.get(room_id)
    
    @classmethod
    def get_by_code(cls, room_code):
        """
        根據房間代碼查詢房間
        
        Args:
            room_code (str): 房間代碼
        
        Returns:
            Room: 房間物件或 None
        """
        return cls.query.filter_by(room_code=room_code).first()
    
    @classmethod
    def get_all(cls, active_only=True, order_by_win_rate=True):
        """
        查詢所有房間
        
        Args:
            active_only (bool): 只查詢開放房間
            order_by_win_rate (bool): 是否按勝率排序
        
        Returns:
            list: 房間物件列表
        """
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        
        if order_by_win_rate:
            query = query.order_by(cls.win_rate.desc())
        
        return query.all()
    
    def update(self, **kwargs):
        """
        更新房間資訊
        
        Args:
            **kwargs: 要更新的欄位
        """
        allowed_fields = {'current_odds', 'total_records', 'win_rate', 'is_active', 'room_name'}
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def delete(self):
        """刪除房間"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    def update_statistics(self, new_result):
        """
        更新房間統計（勝率、開獎次數）
        
        Args:
            new_result (str): 新的開獎結果 ('win' 或 'loss')
        """
        self.total_records += 1
        
        # 計算新的勝率（簡化版：假設 win 記錄數 / 總記錄數）
        # 實際應用可能需要更複雜的統計邏輯
        from app.models.room_record import RoomRecord
        win_count = RoomRecord.query.filter_by(room_id=self.id, result='win').count()
        self.win_rate = float(win_count) / float(self.total_records) * 100 if self.total_records > 0 else 50.0
        
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def get_recent_records(self, limit=10):
        """
        取得最近 N 筆開獎紀錄
        
        Args:
            limit (int): 要取得的紀錄數
        
        Returns:
            list: 最近的 RoomRecord 物件列表
        """
        from app.models.room_record import RoomRecord
        return RoomRecord.query.filter_by(room_id=self.id).order_by(
            RoomRecord.recorded_at.desc()
        ).limit(limit).all()
    
    def calculate_burst_risk(self, window_minutes=5):
        """
        計算快爆風險指標（基於最近 N 分鐘的偏差）
        
        Args:
            window_minutes (int): 計算視窗（分鐘）
        
        Returns:
            float: 快爆風險分數 (0-100)
        """
        from datetime import timedelta
        from app.models.room_record import RoomRecord
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_records = RoomRecord.query.filter(
            RoomRecord.room_id == self.id,
            RoomRecord.recorded_at >= cutoff_time
        ).all()
        
        if not recent_records:
            return 0.0
        
        # 簡化版風險計算：計算平均快爆指標
        avg_burst = sum(float(r.burst_indicator) for r in recent_records) / len(recent_records)
        return min(avg_burst, 100.0)
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'room_code': self.room_code,
            'room_name': self.room_name,
            'current_odds': float(self.current_odds),
            'total_records': self.total_records,
            'win_rate': float(self.win_rate),
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat(),
        }
