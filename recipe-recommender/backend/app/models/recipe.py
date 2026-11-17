from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from ..database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    ingredients = Column(JSON)
    steps = Column(JSON)

    cuisine = Column(String(50))  # 菜系
    region = Column(String(50))   # 地区
    tags = Column(JSON)           # 标签
    meal_type = Column(JSON)      # 适合的用餐时间 ["早餐", "午餐", "晚餐"]
    
    difficulty = Column(Integer)  # 难度 1-5
    prep_time = Column(Integer)   # 准备时间（分钟）
    cook_time = Column(Integer)   # 烹饪时间（分钟）

    nutrition_info = Column(JSON)
    image_url = Column(String(500))

    source = Column(String(20), default="builtin")
    source_url = Column(String(500))

    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
