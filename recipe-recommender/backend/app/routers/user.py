from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from ..database import get_db
from ..models.user import User
from ..models.user_state import UserState
from ..utils.security import get_current_user
from ..services.weather_service import get_weather_by_city

router = APIRouter(prefix="/api/users", tags=["用户"])


class UserUpdate(BaseModel):
    hometown: Optional[str] = None
    current_city: Optional[str] = None
    taste_preferences: Optional[Dict[str, float]] = None
    allergy_info: Optional[List[str]] = None


class UserStateCreate(BaseModel):
    body_feeling: Optional[str] = None
    mood: Optional[str] = None
    craving: Optional[str] = None
    social_media_inspiration: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    hometown: Optional[str] = None
    current_city: Optional[str] = None
    taste_preferences: Optional[Dict] = None
    allergy_info: Optional[List] = None

    class Config:
        from_attributes = True


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_data.hometown is not None:
        current_user.hometown = user_data.hometown
    if user_data.current_city is not None:
        current_user.current_city = user_data.current_city
    if user_data.taste_preferences is not None:
        current_user.taste_preferences = user_data.taste_preferences
    if user_data.allergy_info is not None:
        current_user.allergy_info = user_data.allergy_info

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/state")
async def create_user_state(
    state_data: UserStateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    weather_data = None
    if current_user.current_city:
        weather_data = await get_weather_by_city(current_user.current_city)

    user_state = UserState(
        user_id=current_user.id,
        weather_data=weather_data,
        body_feeling=state_data.body_feeling,
        mood=state_data.mood,
        craving=state_data.craving,
        social_media_inspiration=state_data.social_media_inspiration
    )
    db.add(user_state)
    db.commit()
    db.refresh(user_state)

    return {
        "id": user_state.id,
        "weather": weather_data,
        "created_at": user_state.created_at
    }


@router.get("/states")
def get_user_states(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    states = db.query(UserState).filter(
        UserState.user_id == current_user.id
    ).order_by(UserState.created_at.desc()).limit(limit).all()
    return states
