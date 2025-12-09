# tests/conftest.py
import pytest
import json
from pathlib import Path
from api_test_client import ForumAPIClient

def fetch_and_cache_real_data():
    """Сбор реальных данных для тестов и их кэширование"""
    cache_file = Path(__file__).parent / 'test_data' / 'real_cache.json'
    
    # Если кэш свежий (< 1 часа), используем его
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < 3600:  # 1 час
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # Иначе запрашиваем свежие данные
    client = ForumAPIClient()
    real_data = {
        'stats': client.get_board_stats(),
        'users_sample': client.get_users_list(limit=10),
        'funds': client.get_forum_funds(),
        'timestamp': time.time()
    }
    
    # Сохраняем в кэш
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(real_data, f, ensure_ascii=False, indent=2)
    
    return real_data

@pytest.fixture(scope="session")
def real_forum_data():
    """Фикстура с реальными данными форума"""
    return fetch_and_cache_real_data()

@pytest.fixture
def mock_user_with_real_pattern(real_forum_data):
    """Мок пользователя, но с паттернами из реальных данных"""
    if real_forum_data['users_sample']:
        real_user = real_forum_data['users_sample'][0]
        return {
            'id': 9999,  # Тестовый ID
            'username': 'TestUser_RealPattern',
            'num_posts': real_user.get('num_posts', 0),
            'registered': real_user.get('registered', ''),
            'last_visit': real_user.get('last_visit', ''),
            # остальные поля как в реальных данных
        }
    return None
