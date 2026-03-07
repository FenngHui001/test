#!/usr/bin/env python3
"""
下厨房菜谱爬虫模块
"""
import json
import time
import random
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://hanwuji.xiachufang.com"
CATEGORIES = {
    "荤菜": "/category/40076/",
    "素菜": "/category/40077/",
    "凉菜": "/category/40080/",
    "汤类": "/category/40081/",
    "面食": "/category/40085/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_recipes_from_category(category_url: str, max_recipes: int = 10) -> List[Dict]:
    """
    从分类页面获取菜谱列表
    """
    recipes = []
    try:
        url = BASE_URL + category_url
        print(f"正在获取: {url}")

        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        recipe_items = soup.select(".recipe")
        for item in recipe_items[:max_recipes]:
            try:
                name_elem = item.select_one(".name a")
                if not name_elem:
                    continue

                name = name_elem.get_text(strip=True)
                recipe_url = name_elem.get("href", "")

                # 获取食材（从缩略信息中）
                ingredients_elem = item.select_one(".ing")
                ingredients = []
                if ingredients_elem:
                    ing_text = ingredients_elem.get_text(strip=True)
                    ingredients = [ing.strip() for ing in ing_text.split("/") if ing.strip()]

                recipes.append({
                    "name": name,
                    "ingredients": ingredients if ingredients else ["食材待补充"],
                    "source": "下厨房",
                    "url": BASE_URL + recipe_url if recipe_url else ""
                })

                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"解析菜谱出错: {e}")
                continue

    except Exception as e:
        print(f"获取分类页面出错: {e}")

    return recipes


def update_recipes_database(data_dir: Path = Path("data")):
    """
    更新菜谱数据库
    """
    data_dir.mkdir(exist_ok=True)
    recipes_file = data_dir / "recipes.json"

    # 加载现有数据
    if recipes_file.exists():
        with open(recipes_file, "r", encoding="utf-8") as f:
            all_recipes = json.load(f)
    else:
        all_recipes = {}

    # 从下厨房更新
    print("开始从下厨房获取菜谱...")
    for category, url in CATEGORIES.items():
        print(f"\n获取分类: {category}")
        new_recipes = get_recipes_from_category(url, max_recipes=10)

        if new_recipes:
            if category not in all_recipes:
                all_recipes[category] = []

            # 合并新菜谱，避免重复
            existing_names = {r["name"] for r in all_recipes[category]}
            for recipe in new_recipes:
                if recipe["name"] not in existing_names:
                    all_recipes[category].append(recipe)
                    print(f"  + 添加: {recipe['name']}")

    # 保存
    with open(recipes_file, "w", encoding="utf-8") as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)

    print(f"\n菜谱数据库已更新: {recipes_file}")


def load_recipes(data_dir: Path = Path("data")) -> Dict:
    """
    加载菜谱数据库
    """
    recipes_file = data_dir / "recipes.json"

    if recipes_file.exists():
        with open(recipes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "update":
        update_recipes_database()
    else:
        print("使用方式:")
        print("  python scraper.py update  # 更新菜谱数据库")
        print("\n当前菜谱数据:")
        recipes = load_recipes()
        for category, items in recipes.items():
            print(f"  {category}: {len(items)} 个")
