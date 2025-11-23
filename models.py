from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String(20))
    first_name = Column(String(100))
    username = Column(String(100))
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    ads_watched = Column(Integer, default=0)
    is_watching_ad = Column(Boolean, default=False)
    ad_start_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def can_withdraw(self, amount):
        return self.balance >= amount

class Withdrawal(Base):
    __tablename__ = 'withdrawals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)
    account_info = Column(String(200), nullable=False)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)