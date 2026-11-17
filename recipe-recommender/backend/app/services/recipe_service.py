import json
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models.recipe import Recipe


def get_recipes(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    cuisine: Optional[str] = None,
    tags: Optional[List[str]] = None,
    difficulty: Optional[int] = None,
    search: Optional[str] = None
) -> List[Recipe]:
    """获取食谱列表，支持筛选"""
    query = db.query(Recipe)

    if cuisine:
        query = query.filter(Recipe.cuisine == cuisine)
    if difficulty:
        query = query.filter(Recipe.difficulty <= difficulty)
    if search:
        query = query.filter(
            or_(
                Recipe.name.contains(search),
                Recipe.description.contains(search)
            )
        )
    if tags:
        for tag in tags:
            query = query.filter(Recipe.tags.contains(tag))

    return query.offset(skip).limit(limit).all()


def get_recipe_by_id(db: Session, recipe_id: int) -> Optional[Recipe]:
    """根据ID获取食谱"""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def search_recipes_by_ingredients(db: Session, ingredients: List[str]) -> List[Recipe]:
    """根据食材搜索食谱"""
    recipes = db.query(Recipe).all()
    matched = []

    for recipe in recipes:
        recipe_ingredients = recipe.ingredients or []
        recipe_ingredient_names = [i.get("name", "").lower() for i in recipe_ingredients]

        match_count = sum(
            1 for ing in ingredients
            if any(ing.lower() in name for name in recipe_ingredient_names)
        )

        if match_count > 0:
            matched.append((recipe, match_count))

    matched.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in matched]


def load_builtin_recipes(db: Session, json_path: str):
    """从JSON文件加载内置食谱"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            recipes_data = json.load(f)

        for data in recipes_data:
            existing = db.query(Recipe).filter(Recipe.name == data["name"]).first()
            if not existing:
                recipe = Recipe(
                    name=data["name"],
                    description=data.get("description", ""),
                    ingredients=data.get("ingredients", []),
                    steps=data.get("steps", []),
                    cuisine=data.get("cuisine", ""),
                    region=data.get("region", ""),
                    tags=data.get("tags", []),
                    meal_type=data.get("meal_type", []),
                    difficulty=data.get("difficulty", 3),
                    prep_time=data.get("prep_time", 30),
                    cook_time=data.get("cook_time", 30),
                    nutrition_info=data.get("nutrition_info", {}),
                    image_url=data.get("image_url", ""),
                    source="builtin"
                )
                db.add(recipe)

        db.commit()
    except Exception as e:
        print(f"加载食谱数据失败: {e}")
        db.rollback()
