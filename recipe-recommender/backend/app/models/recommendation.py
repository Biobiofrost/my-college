from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from ..database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)

    score = Column(Float)  # 推荐分数
    reasons = Column(JSON)  # 推荐原因，如 ["天气寒冷适合热汤", "符合您的口味偏好"]
    user_feedback = Column(Integer)  # 用户反馈，1-5分

    created_at = Column(DateTime(timezone=True), server_default=func.now())
