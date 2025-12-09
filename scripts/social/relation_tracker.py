
#!/usr/bin/env python3
"""
Ядро системы отслеживания отношений
Отвечает за парсинг тегов и обновление отношений
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

class RelationTracker:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.load_configs()
        
    def load_configs(self):
        """Загружает конфигурации действий и модификаторов"""
        with open(os.path.join(self.data_dir, "actions_config.json"), "r", encoding="utf-8") as f:
            self.actions_config = json.load(f)
        
        with open(os.path.join(self.data_dir, "modifiers_config.json"), "r", encoding="utf-8") as f:
            self.modifiers_config = json.load(f)
    
    def parse_hashtag(self, hashtag: str) -> Optional[Dict]:
        """
        Парсит хэштег вида #Игрок_действие_модификатор
        Возвращает структурированные данные или None если невалидно
        """
        # Удаляем # в начале
        if hashtag.startswith("#"):
            hashtag = hashtag[1:]
        
        parts = hashtag.split("_")
        
        if len(parts) < 2:
            return None  # Минимум игрок_действие
        
        player_name = parts[0]
        action = parts[1].lower()
        
        # Проверяем, валидно ли действие
        if action not in self.actions_config["actions"]:
            return None
        
        modifiers = []
        if len(parts) > 2:
            modifiers = [mod.lower() for mod in parts[2:] 
                        if mod.lower() in self.modifiers_config["modifiers"]]
        
        return {
            "target_player": player_name,
            "action": action,
            "modifiers": modifiers,
            "raw_tag": f"#{hashtag}"
        }
    
    def extract_hashtags_from_post(self, post_content: str) -> List[Dict]:
        """
        Извлекает все валидные хэштеги взаимодействий из поста
        """
        hashtags = []
        
        # Ищем все хэштеги в посте
        hashtag_pattern = r'#(\w+(?:_\w+)*)'
        matches = re.findall(hashtag_pattern, post_content)
        
        for match in matches:
            parsed = self.parse_hashtag(f"#{match}")
            if parsed:
                hashtags.append(parsed)
        
        return hashtags
    
    def calculate_effect(self, interaction: Dict, description: str = "") -> int:
        """
        Рассчитывает эффект взаимодействия с учётом модификаторов
        """
        action_data = self.actions_config["actions"][interaction["action"]]
        base_effect = action_data["base_effect"]
        
        # Для переменных эффектов анализируем контекст
        if base_effect == "variable":
            base_effect = self._calculate_variable_effect(interaction["action"], description)
        
        # Применяем модификаторы
        total_modifier = 1.0
        for modifier in interaction["modifiers"]:
            if modifier in self.modifiers_config["modifiers"]:
                total_modifier *= self.modifiers_config["modifiers"][modifier]
        
        # Ограничиваем модификаторы
        total_modifier = max(0.3, min(3.0, total_modifier))
        
        # Рассчитываем итоговый эффект
        final_effect = int(base_effect * total_modifier)
        
        # Округляем до ближайшего 5
        if final_effect % 5 != 0:
            final_effect = round(final_effect / 5) * 5
        
        return final_effect
    
    def _calculate_variable_effect(self, action: str, description: str) -> int:
        """Рассчитывает переменный эффект на основе контекста"""
        if action == "долг":
            # Анализируем описание долга
            if any(word in description.lower() for word in ["жизнь", "спасение", "риск"]):
                return 10  # Значительный долг
            else:
                return 5   # Обычный долг
        elif action == "тайна":
            if any(word in description.lower() for word in ["опасный", "секрет", "убийство"]):
                return 10  # Опасная тайна
            else:
                return 5   # Обычная тайна
        
        return 0
    
    def process_player_post(self, player_id: int, player_name: str, 
                           post_content: str, post_date: datetime) -> List[Dict]:
        """
        Обрабатывает пост игрока, извлекает взаимодействия и обновляет отношения
        """
        interactions = self.extract_hashtags_from_post(post_content)
        
        processed = []
        for interaction in interactions:
            # Ищем ID целевого игрока
            target_id = self._find_player_id_by_name(interaction["target_player"])
            if not target_id or target_id == player_id:
                continue  # Пропускаем себя и несуществующих игроков
            
            # Рассчитываем эффект
            effect = self.calculate_effect(interaction, post_content)
            
            # Создаём запись о взаимодействии
            interaction_record = {
                "from_player_id": player_id,
                "from_player_name": player_name,
                "to_player_id": target_id,
                "to_player_name": interaction["target_player"],
                "action": interaction["action"],
                "modifiers": interaction["modifiers"],
                "effect": effect,
                "description": self._extract_description(post_content),
                "post_date": post_date.isoformat(),
                "processed_date": datetime.now().isoformat()
            }
            
            # Сохраняем взаимодействие
            self._save_interaction(interaction_record)
            
            # Обновляем отношения между игроками
            self._update_relationship(player_id, target_id, effect, interaction_record)
            
            processed.append(interaction_record)
        
        return processed
    
    def _find_player_id_by_name(self, player_name: str) -> Optional[int]:
        """Ищет ID игрока по имени (заглушка - нужно интегрировать с реальной БД)"""
        # TODO: Интегрировать с реальной базой игроков
        player_map = {}  # Заглушка
        return player_map.get(player_name.lower())
    
    def _extract_description(self, post_content: str) -> str:
        """Извлекает описание взаимодействия из поста"""
        lines = post_content.strip().split('\n')
        # Берём первые 3 строки без хэштегов как описание
        description_lines = []
        for line in lines[:3]:
            if not line.strip().startswith('#'):
                description_lines.append(line.strip())
        
        return ' '.join(description_lines)[:200]  # Ограничиваем длину
    
    def _save_interaction(self, interaction: Dict):
        """Сохраняет взаимодействие в файл"""
        filename = f"data/social_history/interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{interaction['from_player_id']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(interaction, f, ensure_ascii=False, indent=2)
    
    def _update_relationship(self, player_a_id: int, player_b_id: int, 
                           effect: int, interaction: Dict):
        """Обновляет отношения между двумя игроками"""
        # Загружаем текущие отношения
        rel_file = f"data/players/relationships/{player_a_id}_{player_b_id}.json"
        
        if os.path.exists(rel_file):
            with open(rel_file, 'r', encoding='utf-8') as f:
                relationship = json.load(f)
        else:
            relationship = {
                "player_a_id": player_a_id,
                "player_b_id": player_b_id,
                "total_score": 0,
                "history": [],
                "last_updated": datetime.now().isoformat()
            }
        
        # Обновляем счёт
        relationship["total_score"] += effect
        
        # Ограничиваем от -100 до 100
        relationship["total_score"] = max(-100, min(100, relationship["total_score"]))
        
        # Добавляем в историю
        relationship["history"].append({
            "interaction": interaction,
            "date": datetime.now().isoformat()
        })
        
        # Ограничиваем историю последними 50 записями
        relationship["history"] = relationship["history"][-50:]
        
        # Сохраняем
        relationship["last_updated"] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(rel_file), exist_ok=True)
        with open(rel_file, 'w', encoding='utf-8') as f:
            json.dump(relationship, f, ensure_ascii=False, indent=2)
