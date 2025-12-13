# app/db.py
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.config import settings

DATABASE_URL = settings.DATABASE_URL  # добавь в конфиг

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    template_name = Column(String(100), nullable=True)
    payload_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="queued")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
