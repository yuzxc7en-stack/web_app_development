"""
RoomRecord Model — 房間開獎紀錄

儲存房間的開獎結果，用於趨勢分析、統計與快爆預警
"""

from datetime import datetime
from app.models import db


class RoomRecord(db.Model):
    """房間開獎紀錄模型"""
    
    __tablename__ = 'room_record'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 開獎資訊
    result = db.Column(db.String(20), nullable=False)  # 'odd', 'even', 'high', 'low', 'win', 'loss' 等
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 快爆指標
    burst_indicator = db.Column(db.Integer, nullable=False, default=0)  # 0-100
    
    def __repr__(self):
        return f'<RoomRecord room_id={self.room_id} result={self.result}>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, room_id, user_id, result, burst_indicator=0):
        """
        新增開獎紀錄
        
        Args:
            room_id (int): 房間 ID
            user_id (int): 使用者 ID（誰輸入的紀錄）
            result (str): 開獎結果
            burst_indicator (int, optional): 快爆指標
        
        Returns:
            RoomRecord: 新建立的紀錄物件
        """
        record = cls(
            room_id=room_id,
            user_id=user_id,
            result=result,
            burst_indicator=burst_indicator
        )
        db.session.add(record)
        db.session.commit()
        return record
    
    @classmethod
    def get_by_id(cls, record_id):
        """
        根據 ID 查詢紀錄
        
        Args:
            record_id (int): 紀錄 ID
        
        Returns:
            RoomRecord: 紀錄物件或 None
        """
        return cls.query.get(record_id)
    
    @classmethod
    def get_by_room(cls, room_id, limit=None, order_desc=True):
        """
        查詢特定房間的開獎紀錄
        
        Args:
            room_id (int): 房間 ID
            limit (int, optional): 限制筆數
            order_desc (bool): 是否按時間從新到舊排序
        
        Returns:
            list: 紀錄物件列表
        """
        query = cls.query.filter_by(room_id=room_id)
        
        if order_desc:
            query = query.order_by(cls.recorded_at.desc())
        else:
            query = query.order_by(cls.recorded_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_recent_by_room(cls, room_id, minutes=5):
        """
        查詢房間最近 N 分鐘的開獎紀錄
        
        Args:
            room_id (int): 房間 ID
            minutes (int): 分鐘數
        
        Returns:
            list: 紀錄物件列表
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return cls.query.filter(
            cls.room_id == room_id,
            cls.recorded_at >= cutoff_time
        ).order_by(cls.recorded_at.desc()).all()
    
    def delete(self):
        """刪除紀錄"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    @classmethod
    def calculate_win_streak(cls, room_id, limit=10):
        """
        計算房間的連贏/連敗
        
        Args:
            room_id (int): 房間 ID
            limit (int): 檢查最近 N 筆紀錄
        
        Returns:
            dict: {'win_streak': int, 'loss_streak': int, 'current_trend': str}
        """
        recent_records = cls.get_by_room(room_id, limit=limit, order_desc=True)
        
        if not recent_records:
            return {'win_streak': 0, 'loss_streak': 0, 'current_trend': 'none'}
        
        win_streak = 0
        loss_streak = 0
        current_trend = None
        
        for record in recent_records:
            # 簡化判斷：'win' 相關結果視為勝
            is_win = 'win' in record.result.lower() or record.result in ['odd', 'even']
            
            if is_win:
                if current_trend == 'loss':
                    break
                win_streak += 1
                current_trend = 'win'
            else:
                if current_trend == 'win':
                    break
                loss_streak += 1
                current_trend = 'loss'
        
        return {
            'win_streak': win_streak,
            'loss_streak': loss_streak,
            'current_trend': current_trend or 'none'
        }
    
    @classmethod
    def calculate_statistics(cls, room_id, limit=100):
        """
        計算房間的統計資訊（勝率、平均快爆指標等）
        
        Args:
            room_id (int): 房間 ID
            limit (int): 計算最近 N 筆紀錄
        
        Returns:
            dict: 統計結果
        """
        records = cls.get_by_room(room_id, limit=limit)
        
        if not records:
            return {
                'total': 0,
                'win_rate': 0.0,
                'avg_burst_indicator': 0,
                'max_burst_indicator': 0,
            }
        
        total = len(records)
        win_count = sum(1 for r in records if 'win' in r.result.lower())
        win_rate = (win_count / total * 100) if total > 0 else 0
        avg_burst = sum(r.burst_indicator for r in records) / total
        max_burst = max(r.burst_indicator for r in records)
        
        return {
            'total': total,
            'win_rate': round(win_rate, 2),
            'avg_burst_indicator': round(avg_burst, 2),
            'max_burst_indicator': max_burst,
        }
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'result': self.result,
            'burst_indicator': self.burst_indicator,
            'recorded_at': self.recorded_at.isoformat(),
        }
