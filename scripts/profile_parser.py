"""
Парсер профилей для Whisper of the Void
Извлекает игровые данные (UserFld1) из профилей форума
"""

import requests
import json
import re

def get_user_profile(user_id):
    """Основная функция для получения профиля"""
    url = f"https://warframe.f-rpg.me/member.php?action=profile&uid={user_id}"
    
    try:
        # Делаем запрос как обычный браузер
        headers = {
            'User-Agent': 'Mozilla/5.0 (WotV Parser/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Ищем UserFld1 в исходном коде
            pattern = r"var\s+UserFld1\s*=\s*'([^']+)'"
            match = re.search(pattern, html)
            
            if match:
                json_str = match.group(1).replace('\\"', '"')
                user_data = json.loads(json_str)
                return {
                    'success': True,
                    'user_id': user_id,
                    'data': user_data
                }
            else:
                return {
                    'success': False,
                    'error': 'UserFld1 не найден в HTML'
                }
        else:
            return {
                'success': False,
                'error': f'HTTP ошибка: {response.status_code}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# === ТЕСТИРОВАНИЕ ===
if __name__ == "__main__":
    print("🔍 Тестируем парсинг профиля...")
    print("=" * 40)
    
    # Тестируем на Void (user_id=2)
    result = get_user_profile(2)
    
    if result['success']:
        print("✅ Успешно!")
        print("Данные пользователя:")
        print(json.dumps(result['data'], indent=2, ensure_ascii=False))
    else:
        print("❌ Ошибка:", result['error'])
        print("\nВозможные причины:")
        print("1. Нужна авторизация (куки сессии)")
        print("2. Структура страницы изменилась")
        print("3. У пользователя нет заполненного профиля")
