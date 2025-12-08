"""
Парсер статистики игроков для Whisper of the Void
Извлекает данные из поля статуса (id="profile-title")
"""

import requests
import re

def get_player_stats(user_id):
    """
    Получает данные игрока из публичного профиля на форуме.
    
    Параметры:
        user_id (int): ID пользователя на форуме.
    
    Возвращает:
        dict: Словарь с данными или сообщением об ошибке.
    """
    # Формируем URL профиля
    url = f"https://warframe.f-rpg.me/member.php?action=profile&uid={user_id}"
    
    # Заголовки, чтобы сервер думал, что это браузер
    headers = {
        'User-Agent': 'Mozilla/5.0 (WotV Game Parser/1.0; +https://github.com/voiddevdream/Whisper_of_the_Void)'
    }
    
    try:
        # 1. Загружаем страницу профиля
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Проверим на ошибки HTTP
        
        html = response.text
        
        # 2. Ищем поле статуса по ID
        # Шаблон ищет <li id="profile-title">...<strong>...</strong>...</li>
        title_pattern = r'<li id="profile-title">.*?<strong>(.*?)</strong>'
        match = re.search(title_pattern, html, re.DOTALL)
        
        if not match:
            return {
                'success': False,
                'error': 'Поле статуса (profile-title) не найдено на странице.',
                'user_id': user_id
            }
        
        status_text = match.group(1).strip()
        print(f"[DEBUG] Найден текст статуса: {status_text}")
        
        # 3. Парсим значения: К:+200 З:+13% Ш:+312%
        # Ищем числа после К:, З: и Ш:
        credits_match = re.search(r'К:\s*([+-]?\d+)', status_text)
        infection_match = re.search(r'З:\s*([+-]?\d+)%', status_text)
        whisper_match = re.search(r'Ш:\s*([+-]?\d+)%', status_text)
        
        # 4. Формируем результат
        result = {
            'success': True,
            'user_id': user_id,
            'source': 'profile-title',
            'raw_text': status_text,
            'data': {}
        }
        
        if credits_match:
            result['data']['credits'] = int(credits_match.group(1))
        if infection_match:
            result['data']['infection'] = int(infection_match.group(1))
        if whisper_match:
            result['data']['whisper'] = int(whisper_match.group(1))
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Ошибка сети: {str(e)}',
            'user_id': user_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Неожиданная ошибка: {str(e)}',
            'user_id': user_id
        }

def save_to_json(data, filename):
    """Простая функция для сохранения данных в JSON (для тестов)."""
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Данные сохранены в {filename}")

# === ТЕСТИРОВАНИЕ ===
if __name__ == "__main__":
    print("🔍 Тестируем парсинг данных из поля статуса")
    print("=" * 50)
    
    # Тест 1: Void (user_id=2)
    print("\n1. Тестируем профиль Void (user_id=2):")
    result1 = get_player_stats(2)
    
    if result1['success']:
        print("✅ Успешно!")
        print(f"   Сырой текст: {result1['raw_text']}")
        print(f"   Данные: {result1['data']}")
        
        # Сохраняем для примера
        save_to_json(result1, 'test_void.json')
    else:
        print(f"❌ Ошибка: {result1['error']}")
    
    # Тест 2: Попробуем других пользователей (замени ID)
    print("\n2. Тестируем дополнительный профиль (user_id=4):")
    result2 = get_player_stats(4)  # Попробуй ID другого активного игрока
    
    if result2['success']:
        print("✅ Успешно!")
        print(f"   Данные: {result2['data']}")
    else:
        print(f"❌ Ошибка: {result2['error']}")
    
    print("\n" + "=" * 50)
    print("💡 Советы по использованию:")
    print("1. Запусти скрипт в Google Colab для быстрого теста")
    print("2. Если нужны данные других игроков - укажи их ID")
    print("3. Данные можно сохранять в data/players/user_id.json")
