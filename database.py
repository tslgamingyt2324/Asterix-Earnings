from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Withdrawal
from config import Config

class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def get_user(self, user_id):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            return user
        finally:
            session.close()
    
    def create_user(self, user_data):
        session = self.get_session()
        try:
            existing_user = session.query(User).filter_by(user_id=user_data['user_id']).first()
            if existing_user:
                return existing_user
            
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user
        finally:
            session.close()
    
    def update_user_balance(self, user_id, amount):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.balance += amount
                user.total_earned += amount
                user.ads_watched += 1
                user.is_watching_ad = False
                user.ad_start_time = None
                session.commit()
            return user
        finally:
            session.close()
    
    def create_withdrawal(self, withdrawal_data):
        session = self.get_session()
        try:
            withdrawal = Withdrawal(**withdrawal_data)
            session.add(withdrawal)
            session.commit()
            return withdrawal
        finally:
            session.close()
    
    def set_watching_ad(self, user_id, watching=True):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.is_watching_ad = watching
                if watching:
                    user.ad_start_time = datetime.utcnow()
                else:
                    user.ad_start_time = None
                session.commit()
            return user
        finally:
            session.close()