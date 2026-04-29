"""
BettingRecord Model — 下注紀錄

儲存系統代玩玩家執行的下注操作，記錄每筆下注的結果與損益
"""

from datetime import datetime
from app.models import db


class BettingRecord(db.Model):
    """下注紀錄模型"""
    
    __tablename__ = 'betting_record'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('user_strategy.id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    
    # 下注資訊
    bet_amount = db.Column(db.Numeric(10, 2), nullable=False)
    bet_choice = db.Column(db.String(20), nullable=False)  # 'odd', 'even', 'high', 'low'
    
    # 結果
    bet_result = db.Column(db.String(20), nullable=False, default='pending')  # 'win', 'loss', 'pending', 'cancelled'
    payout = db.Column(db.Numeric(10, 2))  # 所得獲利或損失（可為負數）
    
    # 時間戳記
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<BettingRecord user_id={self.user_id} result={self.bet_result} payout={self.payout}>'
    
    # ============ CRUD 方法 ============
    
    @classmethod
    def create(cls, user_id, strategy_id, room_id, bet_amount, bet_choice):
        """
        新增下注紀錄
        
        Args:
            user_id (int): 使用者 ID
            strategy_id (int): 策略 ID
            room_id (int): 房間 ID
            bet_amount (Decimal): 下注金額
            bet_choice (str): 下注選擇
        
        Returns:
            BettingRecord: 新建立的紀錄物件
        """
        record = cls(
            user_id=user_id,
            strategy_id=strategy_id,
            room_id=room_id,
            bet_amount=bet_amount,
            bet_choice=bet_choice,
            bet_result='pending'
        )
        db.session.add(record)
        db.session.commit()
        return record
    
    @classmethod
    def get_by_id(cls, record_id):
        """
        根據 ID 查詢下注紀錄
        
        Args:
            record_id (int): 紀錄 ID
        
        Returns:
            BettingRecord: 紀錄物件或 None
        """
        return cls.query.get(record_id)
    
    @classmethod
    def get_by_user(cls, user_id, limit=None, order_desc=True):
        """
        查詢使用者的下注紀錄
        
        Args:
            user_id (int): 使用者 ID
            limit (int, optional): 限制筆數
            order_desc (bool): 是否按時間從新到舊排序
        
        Returns:
            list: 下注紀錄物件列表
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if order_desc:
            query = query.order_by(cls.created_at.desc())
        else:
            query = query.order_by(cls.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_today_records(cls, user_id):
        """
        查詢使用者今日的下注紀錄
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            list: 今日下注紀錄物件列表
        """
        from datetime import date
        today = date.today()
        
        return cls.query.filter(
            cls.user_id == user_id,
            db.func.date(cls.created_at) == today
        ).order_by(cls.created_at.desc()).all()
    
    def update_result(self, result, payout):
        """
        更新下注結果
        
        Args:
            result (str): 結果 ('win', 'loss', 'cancelled')
            payout (Decimal): 獲利/損失金額
        """
        self.bet_result = result
        self.payout = payout
        db.session.commit()
    
    def delete(self):
        """刪除紀錄"""
        db.session.delete(self)
        db.session.commit()
    
    # ============ 業務邏輯方法 ============
    
    @classmethod
    def get_today_stats(cls, user_id):
        """
        計算使用者今日的統計資訊
        
        Args:
            user_id (int): 使用者 ID
        
        Returns:
            dict: 統計結果
        """
        today_records = cls.get_today_records(user_id)
        
        if not today_records:
            return {
                'total_bets': 0,
                'total_wagered': 0.0,
                'total_payout': 0.0,
                'net_profit': 0.0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
            }
        
        # 統計完成的下注
        completed = [r for r in today_records if r.bet_result in ['win', 'loss']]
        
        total_wagered = sum(float(r.bet_amount) for r in today_records)
        total_payout = sum(float(r.payout) if r.payout else 0 for r in completed)
        win_count = sum(1 for r in completed if r.bet_result == 'win')
        loss_count = sum(1 for r in completed if r.bet_result == 'loss')
        
        return {
            'total_bets': len(today_records),
            'total_wagered': round(total_wagered, 2),
            'total_payout': round(total_payout, 2),
            'net_profit': round(total_payout - total_wagered, 2),
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': round((win_count / len(completed) * 100) if completed else 0, 2),
        }
    
    @classmethod
    def get_recent_loss_streak(cls, user_id, limit=20):
        """
        計算使用者最近的連敗數
        
        Args:
            user_id (int): 使用者 ID
            limit (int): 檢查最近 N 筆紀錄
        
        Returns:
            int: 連敗數
        """
        recent_bets = cls.query.filter_by(user_id=user_id).filter(
            cls.bet_result.in_(['win', 'loss'])
        ).order_by(cls.created_at.desc()).limit(limit).all()
        
        loss_streak = 0
        for bet in recent_bets:
            if bet.bet_result == 'loss':
                loss_streak += 1
            else:
                break
        
        return loss_streak
    
    @classmethod
    def get_period_stats(cls, user_id, days=7):
        """
        計算使用者最近 N 天的統計
        
        Args:
            user_id (int): 使用者 ID
            days (int): 天數
        
        Returns:
            dict: 統計結果
        """
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        records = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_date,
            cls.bet_result.in_(['win', 'loss'])
        ).all()
        
        if not records:
            return {
                'period_days': days,
                'total_bets': 0,
                'total_wagered': 0.0,
                'total_payout': 0.0,
                'net_profit': 0.0,
                'win_rate': 0.0,
            }
        
        total_wagered = sum(float(r.bet_amount) for r in records)
        total_payout = sum(float(r.payout) if r.payout else 0 for r in records)
        win_count = sum(1 for r in records if r.bet_result == 'win')
        
        return {
            'period_days': days,
            'total_bets': len(records),
            'total_wagered': round(total_wagered, 2),
            'total_payout': round(total_payout, 2),
            'net_profit': round(total_payout - total_wagered, 2),
            'win_rate': round((win_count / len(records) * 100) if records else 0, 2),
        }
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'room_id': self.room_id,
            'bet_amount': float(self.bet_amount),
            'bet_choice': self.bet_choice,
            'bet_result': self.bet_result,
            'payout': float(self.payout) if self.payout else None,
            'created_at': self.created_at.isoformat(),
        }
