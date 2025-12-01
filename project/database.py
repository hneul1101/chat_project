"""
Database layer for Finsearcher
Handles User, Portfolio, and Chat History persistence using SQLite and SQLAlchemy.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import bcrypt
import os

# Database Setup
DB_FILE = "finsearcher.db"
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})  # Investment profile, theme, etc.
    
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ticker = Column(String, nullable=False)
    shares = Column(Integer, default=0)
    avg_price = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="portfolios")

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_logs")

# Initialize Database
def init_db():
    Base.metadata.create_all(engine)

# Data Access Layer
class DBManager:
    def __init__(self):
        self.session = Session()
    
    def close(self):
        self.session.close()

    # User Methods
    def create_user(self, username, password, initial_profile="moderate"):
        if self.get_user(username):
            return None, "이미 존재하는 사용자명입니다."
        
        new_user = User(username=username, settings={"profile": initial_profile})
        new_user.set_password(password)
        self.session.add(new_user)
        try:
            self.session.commit()
            return new_user, None
        except Exception as e:
            self.session.rollback()
            return None, str(e)

    def login_user(self, username, password):
        user = self.get_user(username)
        if user and user.check_password(password):
            return user
        return None

    def get_user(self, username):
        return self.session.query(User).filter_by(username=username).first()

    def update_user_profile(self, user_id, profile):
        user = self.session.query(User).filter_by(id=user_id).first()
        if user:
            settings = dict(user.settings) if user.settings else {}
            settings['profile'] = profile
            user.settings = settings
            self.session.commit()
            return True
        return False

    # Portfolio Methods
    def get_portfolio(self, user_id):
        return self.session.query(Portfolio).filter_by(user_id=user_id).all()

    def add_to_portfolio(self, user_id, ticker, shares, avg_price=0):
        # Check if exists
        item = self.session.query(Portfolio).filter_by(user_id=user_id, ticker=ticker).first()
        if item:
            # Update average price logic could be complex, simple implementation for now
            total_cost = (item.shares * item.avg_price) + (shares * avg_price)
            total_shares = item.shares + shares
            item.shares = total_shares
            item.avg_price = total_cost / total_shares if total_shares > 0 else 0
        else:
            item = Portfolio(user_id=user_id, ticker=ticker, shares=shares, avg_price=avg_price)
            self.session.add(item)
        
        self.session.commit()

    def remove_from_portfolio(self, user_id, ticker):
        self.session.query(Portfolio).filter_by(user_id=user_id, ticker=ticker).delete()
        self.session.commit()
        
    def clear_portfolio(self, user_id):
        self.session.query(Portfolio).filter_by(user_id=user_id).delete()
        self.session.commit()

    # Chat History Methods
    def add_chat_message(self, user_id, role, content):
        msg = ChatLog(user_id=user_id, role=role, content=content)
        self.session.add(msg)
        self.session.commit()

    def get_chat_history(self, user_id, limit=50):
        return self.session.query(ChatLog).filter_by(user_id=user_id).order_by(ChatLog.timestamp.asc()).limit(limit).all()

    def clear_chat_history(self, user_id):
        self.session.query(ChatLog).filter_by(user_id=user_id).delete()
        self.session.commit()

# Initialize on import
init_db()
