#!/usr/bin/env python3
"""
Главный скрипт для обновления социальных профилей
Интегрируется с основным парсером форума
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к нашим модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.social.relation_tracker import RelationTracker
from scripts.social.profile_calculator import SocialProfileCalculator

def main():
    """Основная функция обновления"""
    print("🔄 Начинаю обновление социальных профилей...")
    
    # Инициализируем системы
    tracker = RelationTracker()
    calculator = SocialProfileCalculator()
    
    # 1. Получаем новые посты с форума
    new_posts = get_new_posts_from_forum()
    
    # 2. Обрабатываем каждый пост
    processed_count = 0
    for post in new_posts:
        try:
            interactions = tracker.process_player_post(
                player_id=post['player_id'],
                player_name=post['player_name'],
                post_content=post['content'],
                post_date=post['date']
            )
            
            if interactions:
                processed_count += len(interactions)
                print(f"📝 Обработан пост {post['player_name']}: {len(interactions)} взаимодействий")
                
                # Обновляем профиль игрока
                profile = calculator.calculate_player_profile(post['player_id'])
                print(f"  👤 Обновлён профиль: {profile['icons']['display']} ({profile['total_score']} баллов)")
        
        except Exception as e:
            print(f"❌ Ошибка при обработке поста {post['player_name']}: {e}")
    
    # 3. Обновляем профили всех игроков (на всякий случай)
    all_player_ids = get_all_player_ids()
    
    for player_id in all_player_ids:
        try:
            profile = calculator.calculate_player_profile(player_id)
            print(f"📊 Профиль игрока {player_id}: {profile['icons']['display']}")
        except Exception as e:
            print(f"⚠️ Не удалось обновить профиль игрока {player_id}: {e}")
    
    print(f"✅ Обновление завершено!")
    print(f"📈 Обработано взаимодействий: {processed_count}")
    print(f"👥 Обновлено профилей: {len(all_player_ids)}")

def get_new_posts_from_forum():
    """
    Получает новые посты с форума
    TODO: Интегрировать с реальным API форума
    """
    # Заглушка - возвращаем тестовые данные
    return [
        {
            "player_id": 123,
            "player_name": "RedAlice",
            "content": "Помог Нигану починить генератор. #Negan_помощь_наедине",
            "date": datetime.now()
        },
        {
            "player_id": 456,
            "player_name": "DarkVoid",
            "content": "Украл припасы у Сары. #Sarah_кража_публично",
            "date": datetime.now()
        }
    ]

def get_all_player_ids():
    """Получает ID всех игроков"""
    # TODO: Интегрировать с реальной базой игроков
    return [123, 456, 789]  # Заглушка

if __name__ == "__main__":
    main()
