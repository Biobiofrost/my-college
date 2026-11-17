from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "智能食谱推荐系统"
    DATABASE_URL: str = "sqlite:///./recipe.db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    WEATHER_API_KEY: str = ""
    WEATHER_API_URL: str = "https://devapi.qweather.com/v7"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
