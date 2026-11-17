import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re


def search_recipes_online(keyword: str, limit: int = 5) -> List[Dict]:
    """在线搜索食谱（示例：从下厨房搜索）"""
    try:
        url = "https://www.xiachufang.com/search/"
        params = {"keyword": keyword}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        recipes = []
        recipe_items = soup.select(".recipe-list .recipe-item")[:limit]

        for item in recipe_items:
            try:
                title_elem = item.select_one(".recipe-title a")
                if not title_elem:
                    continue

                name = title_elem.get_text(strip=True)
                link = "https://www.xiachufang.com" + title_elem.get("href", "")

                desc_elem = item.select_one(".recipe-desc")
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                img_elem = item.select_one("img")
                image_url = img_elem.get("src", "") if img_elem else ""

                recipes.append({
                    "name": name,
                    "description": description,
                    "image_url": image_url,
                    "source_url": link,
                    "source": "xiachufang"
                })
            except Exception:
                continue

        return recipes

    except Exception as e:
        print(f"在线搜索失败: {e}")
        return []


def fetch_recipe_detail(url: str) -> Optional[Dict]:
    """获取食谱详情（简化版）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        name_elem = soup.select_one("h1")
        name = name_elem.get_text(strip=True) if name_elem else ""

        ingredients = []
        ingredient_items = soup.select(".ingredient li, .recipe-ingredients li")
        for item in ingredient_items:
            text = item.get_text(strip=True)
            if text:
                parts = re.split(r'\s+', text, maxsplit=1)
                ingredients.append({
                    "name": parts[0],
                    "amount": parts[1] if len(parts) > 1 else ""
                })

        steps = []
        step_items = soup.select(".recipe-step li, .step-content")
        for item in step_items:
            text = item.get_text(strip=True)
            if text:
                steps.append(text)

        return {
            "name": name,
            "ingredients": ingredients,
            "steps": steps,
            "source_url": url,
            "source": "online"
        }

    except Exception as e:
        print(f"获取食谱详情失败: {e}")
        return None
