#!/usr/bin/env python3
"""
菜单生成逻辑模块
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MealConfig:
    """餐次配置"""
    enabled: bool = True
    meat_count: int = 0
    veg_count: int = 0
    cold_count: int = 0
    soup_count: int = 0
    noodle_count: int = 0
    staple_count: int = 1


@dataclass
class MenuConfig:
    """菜单总配置"""
    week_start: str = "周一"
    breakfast: MealConfig = field(default_factory=lambda: MealConfig(enabled=True))
    lunch: MealConfig = field(default_factory=lambda: MealConfig(
        meat_count=2, veg_count=2, cold_count=1, soup_count=1
    ))
    dinner: MealConfig = field(default_factory=lambda: MealConfig(
        meat_count=1, veg_count=2, soup_count=1, noodle_count=1
    ))


@dataclass
class Dish:
    """菜品"""
    name: str
    category: str
    ingredients: List[str]
    source: str = ""


@dataclass
class DailyMenu:
    """一天的菜单"""
    day: str
    date: str
    breakfast: Optional[List[Dish]] = None
    lunch: Optional[List[Dish]] = None
    dinner: Optional[List[Dish]] = None


class MenuGenerator:
    """菜单生成器"""

    DAYS = ["周一", "周二", "周三", "周四", "周五"]

    def __init__(self, recipes: Dict):
        self.recipes = recipes
        self.used_dishes = set()

    def _get_random_dish(self, category: str) -> Optional[Dish]:
        """从指定分类随机获取一个菜品"""
        if category not in self.recipes:
            return None

        dishes = self.recipes[category]
        if not dishes:
            return None

        # 尝试找未使用过的
        for _ in range(10):
            dish = random.choice(dishes)
            key = f"{category}:{dish['name']}"
            if key not in self.used_dishes:
                self.used_dishes.add(key)
                return Dish(
                    name=dish["name"],
                    category=category,
                    ingredients=dish["ingredients"],
                    source=dish.get("source", "")
                )

        # 如果都用过了，随便返回一个
        dish = random.choice(dishes)
        return Dish(
            name=dish["name"],
            category=category,
            ingredients=dish["ingredients"],
            source=dish.get("source", "")
        )

    def _generate_meal(self, config: MealConfig, meal_type: str) -> List[Dish]:
        """生成一餐的菜品"""
        dishes = []

        if meal_type == "breakfast":
            dish = self._get_random_dish("早餐")
            if dish:
                dishes.append(dish)
            return dishes

        # 荤菜
        for _ in range(config.meat_count):
            dish = self._get_random_dish("荤菜")
            if dish:
                dishes.append(dish)

        # 素菜
        for _ in range(config.veg_count):
            dish = self._get_random_dish("素菜")
            if dish:
                dishes.append(dish)

        # 凉菜
        for _ in range(config.cold_count):
            dish = self._get_random_dish("凉菜")
            if dish:
                dishes.append(dish)

        # 汤类
        for _ in range(config.soup_count):
            dish = self._get_random_dish("汤类")
            if dish:
                dishes.append(dish)

        # 面食
        for _ in range(config.noodle_count):
            dish = self._get_random_dish("面食")
            if dish:
                dishes.append(dish)

        # 主食
        for _ in range(config.staple_count):
            dish = self._get_random_dish("主食")
            if dish:
                dishes.append(dish)

        return dishes

    def generate_weekly_menu(self, config: MenuConfig, start_date: Optional[datetime] = None) -> List[DailyMenu]:
        """
        生成一周菜单

        Args:
            config: 菜单配置
            start_date: 开始日期，默认本周一

        Returns:
            一周的菜单列表
        """
        self.used_dishes.clear()

        if start_date is None:
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())

        weekly_menu = []

        for i, day_name in enumerate(self.DAYS):
            current_date = start_date + timedelta(days=i)

            daily = DailyMenu(
                day=day_name,
                date=current_date.strftime("%Y-%m-%d")
            )

            if config.breakfast.enabled:
                daily.breakfast = self._generate_meal(config.breakfast, "breakfast")

            if config.lunch.enabled:
                daily.lunch = self._generate_meal(config.lunch, "lunch")

            if config.dinner.enabled:
                daily.dinner = self._generate_meal(config.dinner, "dinner")

            weekly_menu.append(daily)

        return weekly_menu

    def get_all_ingredients(self, weekly_menu: List[DailyMenu]) -> Dict[str, List[str]]:
        """
        获取一周菜单的所有食材清单

        Returns:
            {菜品名: [食材列表]}
        """
        ingredients = {}

        for daily in weekly_menu:
            for meal_type in ["breakfast", "lunch", "dinner"]:
                dishes = getattr(daily, meal_type, None)
                if dishes:
                    for dish in dishes:
                        ingredients[dish.name] = dish.ingredients

        return ingredients
