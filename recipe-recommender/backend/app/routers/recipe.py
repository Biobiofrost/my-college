from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..models.recipe import Recipe
from ..services.recipe_service import get_recipes, get_recipe_by_id, search_recipes_by_ingredients
from ..services.scraper_service import search_recipes_online

router = APIRouter(prefix="/api/recipes", tags=["食谱"])


@router.get("/")
def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    cuisine: Optional[str] = None,
    difficulty: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    recipes = get_recipes(db, skip=skip, limit=limit, cuisine=cuisine, difficulty=difficulty, search=search)
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "cuisine": r.cuisine,
            "region": r.region,
            "tags": r.tags,
            "meal_type": r.meal_type,
            "difficulty": r.difficulty,
            "prep_time": r.prep_time,
            "cook_time": r.cook_time,
            "image_url": r.image_url,
            "rating": r.rating
        }
        for r in recipes
    ]


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="食谱不存在")
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "cuisine": recipe.cuisine,
        "region": recipe.region,
        "tags": recipe.tags,
        "meal_type": recipe.meal_type,
        "difficulty": recipe.difficulty,
        "prep_time": recipe.prep_time,
        "cook_time": recipe.cook_time,
        "nutrition_info": recipe.nutrition_info,
        "image_url": recipe.image_url,
        "rating": recipe.rating,
        "source": recipe.source,
        "source_url": recipe.source_url
    }


@router.get("/search/by-ingredients")
def search_by_ingredients(
    ingredients: str = Query(..., description="食材，用逗号分隔"),
    db: Session = Depends(get_db)
):
    ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ingredient_list:
        raise HTTPException(status_code=400, detail="请提供至少一个食材")

    recipes = search_recipes_by_ingredients(db, ingredient_list)
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "ingredients": r.ingredients,
            "tags": r.tags,
            "difficulty": r.difficulty
        }
        for r in recipes
    ]


@router.get("/search/online")
def search_online(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20)
):
    results = search_recipes_online(keyword, limit=limit)
    return results
