from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)

    hometown = Column(String(50))  # 家乡
    current_city = Column(String(50))  # 当前城市
    taste_preferences = Column(JSON)  # 口味偏好，如 {"spicy": 0.8, "sweet": 0.3}
    allergy_info = Column(JSON)  # 过敏信息，如 ["peanuts", "seafood"]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
