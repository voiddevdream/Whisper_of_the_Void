#!/usr/bin/env python3
"""
Калькулятор социального профиля
Рассчитывает иконки и статистику на основе взаимодействий
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import glob

class SocialProfileCalculator:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        
        # Настройки иконок
        self.icon_config = {
            "score_ranges": [
                {"min": -100, "max": -60, "icon": "🌑", "name": "Новолуние"},
                {"min": -59, "max": -30, "icon": "🌒", "name": "Убывающий серп"},
                {"min": -29, "max": -10, "icon": "🌓", "name": "Лунный серп"},
                {"min": -9, "max": 9, "icon": "🌔", "name": "Полумесяц"},
                {"min": 10, "max": 29, "icon": "🌕", "name": "Полнолуние"},
                {"min": 30, "max": 59, "icon": "🌤️", "name": "Солнечный свет"},
                {"min": 60, "max": 100, "icon": "☀️", "name": "Яркое солнце"}
            ],
            "category_icons": {
                "betrayal": {"icon": "🗡️", "name": "Кинжал в спине"},
                "hostility": {"icon": "⚔️", "name": "Скрещенные мечи"},
                "contract": {"icon": "🤝", "name": "Рукопожатие"},
                "alliance": {"icon": "🕊️", "name": "Голубь мира"},
                "passion": {"icon": "🔥", "name": "Пламя сердца"}
            }
        }
        
        # Загружаем конфиг действий
        with open(os.path.join(data_dir, "actions_config.json"), "r", encoding="utf-8") as f:
            self.actions_config = json.load(f)
    
    def calculate_player_profile(self, player_id: int) -> Dict:
        """
        Рассчитывает полный социальный профиль игрока
        """
        # Собираем все взаимодействия игрока
        interactions = self._get_player_interactions(player_id)
        
        if not interactions:
            return self._get_default_profile(player_id)
        
        # Рассчитываем статистику
        total_score = 0
        category_scores = {cat: 0 for cat in self.actions_config["categories"]}
        category_counts = {cat: 0 for cat in self.actions_config["categories"]}
        
        for interaction in interactions:
            effect = interaction.get("effect", 0)
            total_score += effect
            
            # Определяем категорию действия
            action = interaction.get("action", "")
            if action in self.actions_config["actions"]:
                category = self.actions_config["actions"][action]["category"]
                category_scores[category] += abs(effect)  # Используем абсолютное значение
                category_counts[category] += 1
        
        # Определяем доминирующую категорию
        dominant_category = max(category_scores.items(), key=lambda x: x[1])[0]
        
        # Рассчитываем проценты
        total_abs_score = sum(category_scores.values())
        if total_abs_score > 0:
            category_percentages = {
                cat: round((score / total_abs_score) * 100)
                for cat, score in category_scores.items()
            }
        else:
            category_percentages = {cat: 0 for cat in category_scores}
        
        # Определяем иконки
        icons = self._determine_icons(total_score, dominant_category)
        
        # Генерируем описание
        description = self._generate_description(total_score, dominant_category, category_percentages)
        
        # Формируем профиль
        profile = {
            "player_id": player_id,
            "calculated_at": datetime.now().isoformat(),
            "total_score": total_score,
            "interaction_count": len(interactions),
            "icons": icons,
            "category_distribution": {
                "scores": category_scores,
                "counts": category_counts,
                "percentages": category_percentages
            },
            "dominant_category": dominant_category,
            "dominant_category_name": self.actions_config["categories"][dominant_category]["name"],
            "description": description,
            "trend": self._calculate_trend(player_id, total_score)
        }
        
        # Сохраняем профиль
        self._save_profile(player_id, profile)
        
        return profile
    
    def _get_player_interactions(self, player_id: int) -> List[Dict]:
        """Получает все взаимодействия игрока"""
        interactions = []
        
        # Ищем файлы взаимодействий
        pattern = os.path.join(self.data_dir, "social_history", f"*_{player_id}.json")
        files = glob.glob(pattern)
        
        # Также ищем файлы, где player_id - отправитель
        pattern2 = os.path.join(self.data_dir, "social_history", f"interaction_*_{player_id}.json")
        files.extend(glob.glob(pattern2))
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    interaction = json.load(f)
                    interactions.append(interaction)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        return interactions
    
    def _determine_icons(self, total_score: int, dominant_category: str) -> Dict:
        """Определяет иконки для профиля"""
        # Основная иконка по баллу
        main_icon = "🌔"
        main_name = "Полумесяц"
        
        for range_config in self.icon_config["score_ranges"]:
            if range_config["min"] <= total_score <= range_config["max"]:
                main_icon = range_config["icon"]
                main_name = range_config["name"]
                break
        
        # Подтип по категории
        category_icon = self.icon_config["category_icons"].get(
            dominant_category, 
            {"icon": "•", "name": ""}
        )
        
        return {
            "main": {"icon": main_icon, "name": main_name},
            "sub": {"icon": category_icon["icon"], "name": category_icon["name"]},
            "display": f"{main_icon}{category_icon['icon']}",
            "full_name": f"{main_name} • {category_icon['name']}"
        }
    
    def _generate_description(self, score: int, dominant_category: str, 
                            percentages: Dict) -> str:
        """Генерирует описание профиля"""
        descriptions = {
            "betrayal": [
                "Опасный предатель. Известен вероломными поступками.",
                "Ненадёжный союзник. Склонен нарушать клятвы.",
                "Тёмная душа. Доверие для него - слабость."
            ],
            "hostility": [
                "Конфликтная личность. Часто вступает в противостояния.",
                "Воинственный нрав. Решает споры силой.",
                "Агрессивный характер. Лучше не переходить ему дорогу."
            ],
            "contract": [
                "Расчётливый переговорщик. Всё взвешивает.",
                "Прагматик. Ценит договоры выше эмоций.",
                "Хладнокровный стратег. Играет по правилам, которые сам устанавливает."
            ],
            "alliance": [
                "Надёжный союзник. Всегда придёт на помощь.",
                "Верный друг. Ценит доверие выше выгоды.",
                "Светлая душа. Верит в лучшее даже в кромешной тьме."
            ],
            "passion": [
                "Эмоциональная натура. Живёт чувствами, а не расчётом.",
                "Страстная душа. Любовь и ненависть для него - две стороны одной медали.",
                "Глубоко чувствующий. Его эмоции - и сила, и слабость."
            ]
        }
        
        # Выбираем описание по категории
        category_descriptions = descriptions.get(dominant_category, ["Загадочная личность."])
        
        # Добавляем оценку по баллу
        if score <= -50:
            intensity = "Абсолютно "
        elif score <= -20:
            intensity = "Явно "
        elif score <= -5:
            intensity = "Слегка "
        elif score <= 5:
            intensity = ""
        elif score <= 20:
            intensity = "Достаточно "
        elif score <= 50:
            intensity = "Очень "
        else:
            intensity = "Невероятно "
        
        # Формируем итоговое описание
        base_desc = category_descriptions[0]
        return f"{intensity}{base_desc.lower()}"
    
    def _calculate_trend(self, player_id: int, current_score: int) -> str:
        """Рассчитывает тренд изменения профиля"""
        # Загружаем историю профилей
        profile_history = self._load_profile_history(player_id)
        
        if len(profile_history) < 2:
            return "stable"
        
        # Сравниваем с предыдущим профилем
        previous_score = profile_history[-2].get("total_score", 0)
        
        if current_score > previous_score + 10:
            return "improving"
        elif current_score < previous_score - 10:
            return "worsening"
        else:
            return "stable"
    
    def _load_profile_history(self, player_id: int) -> List[Dict]:
        """Загружает историю профилей игрока"""
        history_file = os.path.join(self.data_dir, "social_history", f"profile_history_{player_id}.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_profile(self, player_id: int, profile: Dict):
        """Сохраняет профиль игрока"""
        # Основной файл профиля
        profile_file = os.path.join(self.data_dir, "players", f"social_profile_{player_id}.json")
        os.makedirs(os.path.dirname(profile_file), exist_ok=True)
        
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        
        # Добавляем в историю
        history_file = os.path.join(self.data_dir, "social_history", f"profile_history_{player_id}.json")
        history = self._load_profile_history(player_id)
        history.append({
            "date": profile["calculated_at"],
            "total_score": profile["total_score"],
            "dominant_category": profile["dominant_category"]
        })
        
        # Ограничиваем историю последними 20 записями
        history = history[-20:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def _get_default_profile(self, player_id: int) -> Dict:
        """Возвращает профиль по умолчанию для новых игроков"""
        return {
            "player_id": player_id,
            "calculated_at": datetime.now().isoformat(),
            "total_score": 0,
            "interaction_count": 0,
            "icons": {
                "main": {"icon": "🌔", "name": "Полумесяц"},
                "sub": {"icon": "•", "name": "Неизвестно"},
                "display": "🌔•",
                "full_name": "Полумесяц • Неизвестно"
            },
            "category_distribution": {
                "scores": {cat: 0 for cat in self.actions_config["categories"]},
                "counts": {cat: 0 for cat in self.actions_config["categories"]},
                "percentages": {cat: 0 for cat in self.actions_config["categories"]}
            },
            "dominant_category": "contract",
            "dominant_category_name": "Договор",
            "description": "Новый в Хёльвании. Его социальный профиль ещё формируется.",
            "trend": "stable"
        }
