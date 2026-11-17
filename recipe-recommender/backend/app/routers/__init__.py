from .auth import router as auth_router
from .user import router as user_router
from .recipe import router as recipe_router
from .recommend import router as recommend_router

__all__ = ["auth_router", "user_router", "recipe_router", "recommend_router"]
