from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .database import engine, Base
from .routers import auth_router, user_router, recipe_router, recommend_router
from .services.recipe_service import load_builtin_recipes
from .database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "recipes.json")
        if os.path.exists(json_path):
            load_builtin_recipes(db, json_path)
    finally:
        db.close()

    yield


app = FastAPI(
    title="智能食谱推荐系统",
    description="基于用户状态和环境因素的个性化食谱推荐API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(recipe_router)
app.include_router(recommend_router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "智能食谱推荐系统运行正常"}


frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")
