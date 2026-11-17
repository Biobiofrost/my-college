from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from ..database import Base


class UserState(Base):
    __tablename__ = "user_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    weather_data = Column(JSON)  # 天气数据，如 {"temp": 25, "humidity": 60, "condition": "晴"}
    body_feeling = Column(String(200))  # 身体感受，如 "感觉干燥"
    mood = Column(String(100))  # 情绪，如 "想吃点辣的提神"
    craving = Column(String(200))  # 想吃什么，如 "火锅"
    social_media_inspiration = Column(Text)  # 社交媒体灵感，如 "刷到一个红烧肉视频"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
