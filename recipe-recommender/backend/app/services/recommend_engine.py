from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models.user import User
from ..models.recipe import Recipe
from ..models.user_state import UserState
from ..models.recommendation import Recommendation
from .weather_service import analyze_weather_for_recipe
from datetime import datetime


def get_current_meal_type() -> str:
    """根据当前时间判断用餐类型"""
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return "早餐"
    elif 10 <= hour < 14:
        return "午餐"
    elif 14 <= hour < 17:
        return "下午茶"
    elif 17 <= hour < 21:
        return "晚餐"
    else:
        return "夜宵"


def get_recommendations(
    db: Session,
    user: Optional[User] = None,
    user_state: Optional[UserState] = None,
    location: Optional[str] = None,
    mode: str = "normal",
    limit: int = 10
) -> List[Dict]:
    """
    为用户生成个性化推荐
    
    mode:
    - normal: 普通模式（登录用户）
    - tourist: 旅游模式（未登录，推荐当地特色）
    - migrant: 异地工作模式（登录，家乡与当前城市不同）
    """
    recipes = db.query(Recipe).all()
    
    if not recipes:
        return []

    weather_factors = {}
    if user_state and user_state.weather_data:
        weather_factors = analyze_weather_for_recipe(user_state.weather_data)

    current_meal = get_current_meal_type()

    scored_recipes = []
    for recipe in recipes:
        score, reasons = calculate_recipe_score(
            recipe=recipe,
            user=user,
            user_state=user_state,
            weather_factors=weather_factors,
            location=location,
            mode=mode,
            current_meal=current_meal
        )
        scored_recipes.append({
            "recipe": recipe,
            "score": score,
            "reasons": reasons,
            "meal_type": current_meal
        })

    scored_recipes.sort(key=lambda x: x["score"], reverse=True)
    return scored_recipes[:limit]


def calculate_recipe_score(
    recipe: Recipe,
    user: Optional[User] = None,
    user_state: Optional[UserState] = None,
    weather_factors: Dict[str, float] = None,
    location: Optional[str] = None,
    mode: str = "normal",
    current_meal: str = "午餐"
) -> tuple[float, List[str]]:
    """计算单个食谱的推荐分数"""
    score = 0.5
    reasons = []

    # 用餐时间匹配 (权重: 15%)
    meal_score = calculate_meal_score(recipe, current_meal)
    score += meal_score * 0.15
    if meal_score > 0.7:
        reasons.append(f"适合{current_meal}")

    # 天气因素 (权重: 25%)
    if weather_factors:
        weather_score = calculate_weather_score(recipe, weather_factors)
        score += weather_score * 0.25
        if weather_score > 0.5:
            reasons.append("适合当前天气")

    if mode == "tourist":
        # 旅游模式：推荐当地特色菜
        local_score = calculate_local_score(recipe, location)
        score += local_score * 0.4
        if local_score > 0.7:
            reasons.append("当地特色美食")
        
        popular_score = calculate_popular_score(recipe)
        score += popular_score * 0.2
        if popular_score > 0.7:
            reasons.append("热门推荐")

    elif mode == "migrant" and user:
        # 异地工作模式：兼顾家乡口味和当地特色
        hometown_score = calculate_homesick_score(recipe, user)
        score += hometown_score * 0.3
        if hometown_score > 0.7:
            reasons.append("家乡味道")
        
        local_adapt_score = calculate_local_adapt_score(recipe, location)
        score += local_adapt_score * 0.2
        if local_adapt_score > 0.5:
            reasons.append("融入当地")

    elif user:
        # 普通登录模式
        preference_score = calculate_preference_score(recipe, user)
        score += preference_score * 0.25
        if preference_score > 0.5:
            reasons.append("符合您的口味偏好")

        region_score = calculate_region_score(recipe, user)
        score += region_score * 0.2
        if region_score > 0.5:
            reasons.append("符合您的地域口味")

    # 用户状态匹配 (权重: 15%)
    if user_state:
        state_score = calculate_state_score(recipe, user_state)
        score += state_score * 0.15
        if state_score > 0.5:
            reasons.append("符合您当前的需求")

    # 食谱质量 (权重: 10%)
    quality_score = calculate_quality_score(recipe)
    score += quality_score * 0.10

    if not reasons:
        reasons.append("为您推荐")

    return min(score, 1.0), reasons


def calculate_meal_score(recipe: Recipe, current_meal: str) -> float:
    """计算用餐时间匹配分"""
    meal_types = recipe.meal_type or []
    if current_meal in meal_types:
        return 1.0
    
    # 早餐适合清淡、粥类
    if current_meal == "早餐":
        if any(tag in (recipe.tags or []) for tag in ["早餐", "粥", "面食", "点心"]):
            return 0.8
        return 0.3
    
    # 午餐晚餐可以吃正餐
    if current_meal in ["午餐", "晚餐"]:
        if any(tag in (recipe.tags or []) for tag in ["热菜", "凉拌", "汤"]):
            return 0.7
        return 0.5
    
    return 0.5


def calculate_weather_score(recipe: Recipe, weather_factors: Dict[str, float]) -> float:
    """计算天气匹配分"""
    if not recipe.tags:
        return 0.5

    score = 0.0
    count = 0

    tag_factor_mapping = {
        "汤": "hot_soup",
        "炖": "hot_soup",
        "热菜": "hot_soup",
        "粥": "hot_soup",
        "凉拌": "cold_dish",
        "冷菜": "cold_dish",
        "辣": "spicy",
        "清淡": "light",
        "滋润": "moistening",
        "解暑": "cold_dish",
        "暖身": "hot_soup"
    }

    for tag in (recipe.tags or []):
        factor_key = tag_factor_mapping.get(tag)
        if factor_key and factor_key in weather_factors:
            score += weather_factors[factor_key]
            count += 1

    return score / count if count > 0 else 0.5


def calculate_local_score(recipe: Recipe, location: Optional[str]) -> float:
    """计算当地特色分（旅游模式用）"""
    if not location or not recipe.region:
        return 0.5
    
    # 如果食谱的地区与当前位置匹配
    if recipe.region == location or recipe.region == "全国":
        return 1.0
    
    # 城市到省份的映射
    city_to_province = {
        "北京": "北京", "上海": "上海", "广州": "广东", "深圳": "广东",
        "成都": "四川", "重庆": "重庆", "西安": "陕西", "杭州": "浙江",
        "南京": "江苏", "武汉": "湖北", "长沙": "湖南", "天津": "天津",
        "哈尔滨": "黑龙江", "沈阳": "辽宁", "大连": "辽宁",
        "昆明": "云南", "贵阳": "贵州", "南宁": "广西",
        "兰州": "甘肃", "乌鲁木齐": "新疆", "拉萨": "西藏",
        "济南": "山东", "青岛": "山东", "厦门": "福建", "福州": "福建"
    }
    
    province = city_to_province.get(location, location)
    if recipe.region == province:
        return 0.9
    
    return 0.3


def calculate_popular_score(recipe: Recipe) -> float:
    """计算热门度分（旅游模式用）"""
    # 经典菜和特色菜得分高
    popular_tags = ["经典", "特色", "名菜", "代表"]
    tags = recipe.tags or []
    
    for tag in tags:
        if tag in popular_tags:
            return 0.9
    
    # 评分高的菜也推荐
    if recipe.rating and recipe.rating > 4.0:
        return 0.8
    
    return 0.5


def calculate_homesick_score(recipe: Recipe, user: User) -> float:
    """计算思乡分（异地工作模式用）"""
    if not user.hometown or not recipe.region:
        return 0.5
    
    # 家乡菜得分高
    if recipe.region == user.hometown:
        return 1.0
    
    # 同一菜系也得分
    region_cuisine_mapping = {
        "四川": "川菜", "重庆": "川菜", "湖南": "湘菜", "湖北": "鄂菜",
        "广东": "粤菜", "广西": "粤菜", "福建": "闽菜",
        "山东": "鲁菜", "河北": "鲁菜", "北京": "京菜",
        "上海": "本帮菜", "江苏": "苏菜", "浙江": "浙菜",
        "东北": "东北菜", "黑龙江": "东北菜", "吉林": "东北菜", "辽宁": "东北菜",
        "陕西": "西北菜", "甘肃": "西北菜", "新疆": "西北菜", "宁夏": "西北菜",
        "云南": "滇菜", "贵州": "黔菜", "广西": "桂菜",
        "天津": "津菜"
    }
    
    hometown_cuisine = region_cuisine_mapping.get(user.hometown)
    if hometown_cuisine and recipe.cuisine == hometown_cuisine:
        return 0.8
    
    return 0.3


def calculate_local_adapt_score(recipe: Recipe, location: Optional[str]) -> float:
    """计算融入当地分（异地工作模式用）"""
    if not location or not recipe.region:
        return 0.5
    
    # 当地菜得分
    if recipe.region == location:
        return 0.8
    
    # 全国性菜品也得分
    if recipe.region == "全国":
        return 0.6
    
    return 0.3


def calculate_preference_score(recipe: Recipe, user: User) -> float:
    """计算口味偏好匹配分"""
    if not user.taste_preferences or not recipe.tags:
        return 0.5

    score = 0.0
    count = 0

    tag_mapping = {
        "辣": "spicy",
        "甜": "sweet",
        "酸": "sour",
        "咸": "salty",
        "清淡": "light",
        "重口味": "strong"
    }

    for tag in (recipe.tags or []):
        pref_key = tag_mapping.get(tag)
        if pref_key and pref_key in user.taste_preferences:
            score += user.taste_preferences[pref_key]
            count += 1

    return score / count if count > 0 else 0.5


def calculate_region_score(recipe: Recipe, user: User) -> float:
    """计算地域匹配分"""
    if not recipe.cuisine or not user.hometown:
        return 0.5

    region_cuisine_mapping = {
        "四川": "川菜", "重庆": "川菜", "湖南": "湘菜", "湖北": "鄂菜",
        "广东": "粤菜", "广西": "粤菜", "福建": "闽菜",
        "山东": "鲁菜", "河北": "鲁菜", "北京": "京菜",
        "上海": "本帮菜", "江苏": "苏菜", "浙江": "浙菜",
        "东北": "东北菜", "黑龙江": "东北菜", "吉林": "东北菜", "辽宁": "东北菜",
        "陕西": "西北菜", "甘肃": "西北菜", "新疆": "西北菜", "宁夏": "西北菜",
        "云南": "滇菜", "贵州": "黔菜", "广西": "桂菜",
        "天津": "津菜"
    }

    hometown_cuisine = region_cuisine_mapping.get(user.hometown, "")
    current_cuisine = region_cuisine_mapping.get(user.current_city, "")

    score = 0.5

    if recipe.cuisine == hometown_cuisine:
        score += 0.3
    if hometown_cuisine and hometown_cuisine != current_cuisine:
        if recipe.cuisine == hometown_cuisine:
            score += 0.2

    return min(score, 1.0)


def calculate_state_score(recipe: Recipe, user_state: UserState) -> float:
    """计算用户状态匹配分"""
    score = 0.5

    if user_state.craving:
        craving_lower = user_state.craving.lower()
        recipe_name_lower = recipe.name.lower()
        recipe_tags = [t.lower() for t in (recipe.tags or [])]

        if craving_lower in recipe_name_lower:
            score += 0.4
        elif any(craving_lower in tag for tag in recipe_tags):
            score += 0.3

    if user_state.body_feeling:
        feeling_lower = user_state.body_feeling.lower()
        if "干燥" in feeling_lower and "滋润" in (recipe.tags or []):
            score += 0.2
        if "冷" in feeling_lower and any(t in (recipe.tags or []) for t in ["汤", "热菜", "暖身"]):
            score += 0.2
        if "热" in feeling_lower and any(t in (recipe.tags or []) for t in ["凉拌", "清淡", "解暑"]):
            score += 0.2

    if user_state.social_media_inspiration:
        inspiration_lower = user_state.social_media_inspiration.lower()
        if any(word in inspiration_lower for word in [recipe.name.lower()] + [t.lower() for t in (recipe.tags or [])]):
            score += 0.3

    return min(score, 1.0)


def calculate_quality_score(recipe: Recipe) -> float:
    """计算食谱质量分"""
    score = 0.5
    
    if recipe.rating:
        score = recipe.rating / 5.0
    
    # 难度适中的菜更受欢迎
    if recipe.difficulty and 2 <= recipe.difficulty <= 3:
        score += 0.1
    
    return min(score, 1.0)


def save_recommendation(db: Session, user_id: int, recipe_id: int, score: float, reasons: List[str]):
    """保存推荐记录"""
    rec = Recommendation(
        user_id=user_id,
        recipe_id=recipe_id,
        score=score,
        reasons=reasons
    )
    db.add(rec)
    db.commit()
    return rec


def update_feedback(db: Session, recommendation_id: int, feedback: int):
    """更新用户反馈"""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if rec:
        rec.user_feedback = feedback
        db.commit()
    return rec
