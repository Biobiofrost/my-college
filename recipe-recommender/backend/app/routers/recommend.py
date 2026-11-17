from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.user_state import UserState
from ..utils.security import get_current_user
from ..services.recommend_engine import get_recommendations, save_recommendation, update_feedback, get_current_meal_type
from ..services.weather_service import get_weather_by_city, get_location_by_ip

router = APIRouter(prefix="/api/recommend", tags=["推荐"])


class FeedbackRequest(BaseModel):
    recommendation_id: int
    feedback: int  # 1-5


class GuestStateRequest(BaseModel):
    city: Optional[str] = None
    body_feeling: Optional[str] = None
    craving: Optional[str] = None
    social_media_inspiration: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    # 优先从代理头获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 尝试从其他头获取
    cf_connecting = request.headers.get("CF-Connecting-IP")
    if cf_connecting:
        return cf_connecting
    
    return request.client.host or "127.0.0.1"


@router.get("/location")
async def get_client_location(request: Request):
    """获取客户端位置和天气信息"""
    client_ip = get_client_ip(request)
    
    # 获取位置信息
    location_info = await get_location_by_ip(client_ip)
    
    city = ""
    if location_info:
        city = location_info.get("city", "")
    
    # 如果IP定位失败，使用默认城市
    if not city:
        city = "北京"
    
    # 获取天气信息
    weather_data = await get_weather_by_city(city)
    
    # 获取用餐类型
    meal_type = get_current_meal_type()
    
    return {
        "ip": client_ip,
        "city": city,
        "region": location_info.get("region", "") if location_info else "",
        "weather": weather_data,
        "meal_type": meal_type,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d")
    }


@router.get("/meal-type")
def get_meal_type():
    """获取当前用餐类型"""
    return {"meal_type": get_current_meal_type()}


@router.get("/today")
async def get_today_recommendations(
    request: Request,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """登录用户获取推荐"""
    latest_state = db.query(UserState).filter(
        UserState.user_id == current_user.id
    ).order_by(UserState.created_at.desc()).first()

    # 判断是否为异地工作模式
    mode = "normal"
    if current_user.hometown and current_user.current_city:
        if current_user.hometown != current_user.current_city:
            mode = "migrant"

    recommendations = get_recommendations(
        db, current_user, latest_state, 
        location=current_user.current_city,
        mode=mode, 
        limit=limit
    )

    result = []
    for rec in recommendations:
        recipe = rec["recipe"]
        saved = save_recommendation(
            db, current_user.id, recipe.id, rec["score"], rec["reasons"]
        )
        result.append({
            "recommendation_id": saved.id,
            "recipe": {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "cuisine": recipe.cuisine,
                "region": recipe.region,
                "tags": recipe.tags,
                "meal_type": recipe.meal_type,
                "difficulty": recipe.difficulty,
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "image_url": recipe.image_url,
            },
            "score": rec["score"],
            "reasons": rec["reasons"],
            "meal_type": rec["meal_type"],
            "mode": mode
        })

    return result


@router.post("/guest")
async def get_guest_recommendations(
    request: Request,
    state: GuestStateRequest,
    db: Session = Depends(get_db)
):
    """游客模式获取推荐（不需要登录）"""
    city = state.city
    
    # 如果没有提供城市，尝试通过IP定位
    if not city:
        client_ip = get_client_ip(request)
        location_info = await get_location_by_ip(client_ip)
        if location_info:
            city = location_info.get("city", "")
    
    # 获取天气信息
    weather_data = None
    if city:
        weather_data = await get_weather_by_city(city)

    # 构造状态对象
    user_state = None
    if state.body_feeling or state.craving or state.social_media_inspiration or weather_data:
        user_state = UserState(
            user_id=0,
            weather_data=weather_data,
            body_feeling=state.body_feeling,
            craving=state.craving,
            social_media_inspiration=state.social_media_inspiration
        )

    recommendations = get_recommendations(
        db, None, user_state, 
        location=city,
        mode="tourist", 
        limit=10
    )

    current_meal = get_current_meal_type()

    result = []
    for rec in recommendations:
        recipe = rec["recipe"]
        result.append({
            "recipe": {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "cuisine": recipe.cuisine,
                "region": recipe.region,
                "tags": recipe.tags,
                "meal_type": recipe.meal_type,
                "difficulty": recipe.difficulty,
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "image_url": recipe.image_url,
            },
            "score": rec["score"],
            "reasons": rec["reasons"],
            "meal_type": current_meal,
            "mode": "tourist",
            "location": city,
            "weather": weather_data
        })

    return result


@router.get("/meal-type")
def get_meal_type():
    """获取当前用餐类型"""
    return {"meal_type": get_current_meal_type()}


@router.post("/feedback")
def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if feedback_data.feedback < 1 or feedback_data.feedback > 5:
        raise HTTPException(status_code=400, detail="反馈分数必须在1-5之间")

    rec = update_feedback(db, feedback_data.recommendation_id, feedback_data.feedback)
    if not rec:
        raise HTTPException(status_code=404, detail="推荐记录不存在")

    return {"message": "反馈已提交"}


@router.get("/history")
def get_recommendation_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..models.recommendation import Recommendation

    recs = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id
    ).order_by(Recommendation.created_at.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "recipe_id": r.recipe_id,
            "score": r.score,
            "reasons": r.reasons,
            "user_feedback": r.user_feedback,
            "created_at": r.created_at
        }
        for r in recs
    ]
