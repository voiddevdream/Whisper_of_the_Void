# tests/api_test_client.py
import requests
import time
from typing import Optional, Dict, List

class ForumAPIClient:
    def __init__(self, base_url: str = "https://warframe.f-rpg.me/api.php"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TestBot/1.0 (Test Suite)'
        })
    
    def _make_request(self, method: str, **params) -> Optional[Dict]:
        """Базовый метод для всех API-запросов"""
        params['method'] = method
        params['format'] = 'json'
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Обработка возможных ошибок API
            if 'error' in data:
                print(f"API Error: {data['error']}")
                return None
                
            return data.get('response', {})
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except ValueError as e:
            print(f"JSON decode error: {e}")
            return None
    
    # Методы для тестирования
    def get_board_stats(self) -> Optional[Dict]:
        return self._make_request('board.get', fields='total_users,total_posts,active_users')
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        return self._make_request('users.get', user_id=str(user_id))
    
    def get_users_list(self, limit: int = 5, skip: int = 0) -> Optional[List]:
        return self._make_request(
            'users.orderedList',
            sort_by='registered',
            sort_dir='desc',
            limit=limit,
            skip=skip
        )
    
    def get_forum_funds(self) -> Optional[Dict]:
        return self._make_request('board.getFunds')
