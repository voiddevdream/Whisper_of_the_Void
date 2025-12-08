"""
ЯДРО Whisper of the Void
Объединяет парсинг списка игроков и постов через API
"""

import requests
import json
import time
from datetime import datetime, timedelta
from userlist_parser import fetch_all_players  # Импортируем наш парсер

class WotVCore:
    def __init__(self):
        self.api_url = "https://warframe.f-rpg.me/api.php"
        self.players_file = "data/players/all_players.json"
        self.posts_file = "data/latest_posts.json"
        
    def get_recent_posts(self, hours=24):
        """
        Получает свежие посты за последние N часов через API
        """
        print(f"📝 Получаем посты за последние {hours} часов...")
        
        # Рассчитываем timestamp для фильтрации
        cutoff_time = int(time.time()) - (hours * 3600)
        
        # Параметры API запроса
        params = {
            'method': 'post.get',
            'sort_by': 'id',
            'sort_dir': 'desc',
            'limit': 100  # Можно увеличить при необходимости
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('response', [])
                
                # Фильтруем по времени
                recent_posts = [
                    post for post in posts 
                    if int(post.get('posted', 0)) > cutoff_time
                ]
                
                print(f"✅ Найдено {len(recent_posts)} новых постов (всего {len(posts)})")
                return recent_posts
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка при получении постов: {e}")
            return []
    
    def analyze_posts_for_stats(self, posts):
        """
        Анализирует посты для обновления статистики игроков
        """
        if not posts:
            return {}
        
        print("📊 Анализируем активность в постах...")
        
        # Считаем посты по игрокам
        user_activity = {}
        
        for post in posts:
            user_id = post.get('user_id')
            if not user_id:
                continue
            
            user_id = int(user_id)
            
            if user_id not in user_activity:
                user_activity[user_id] = {
                    'post_count': 0,
                    'last_post': post.get('posted'),
                    'topics': set()
                }
            
            user_activity[user_id]['post_count'] += 1
            user_activity[user_id]['topics'].add(post.get('topic_id'))
        
        # Преобразуем в удобный формат
        for user_id, data in user_activity.items():
            data['unique_topics'] = len(data['topics'])
            del data['topics']  # Удаляем set, он не сериализуется в JSON
        
        print(f"📈 Активность {len(user_activity)} игроков")
        return user_activity
    
    def calculate_daily_changes(self, players_data, user_activity):
        """
        Рассчитывает ежедневные изменения показателей
        """
        print("🧮 Рассчитываем ежедневные изменения...")
        
        changes = {}
        
        for user_id, player_data in players_data.items():
            user_id_int = int(user_id)
            activity = user_activity.get(user_id_int, {})
            
            # Базовые изменения
            daily_changes = {
                'credits': 0,
                'infection': 0.2,  # Базовый рост заражения в день
                'whisper': 0
            }
            
            # Бонусы за активность
            if activity:
                # За каждый пост +5 кредитов
                daily_changes['credits'] += activity.get('post_count', 0) * 5
                
                # За каждый уникальный топик +2% к шёпоту (но риск!)
                daily_changes['whisper'] += activity.get('unique_topics', 0) * 2
                
                # Активные игроки медленнее заражаются
                daily_changes['infection'] -= min(0.15, activity.get('post_count', 0) * 0.03)
            
            changes[user_id] = daily_changes
        
        return changes
    
    def update_players_data(self, changes):
        """
        Обновляет данные игроков на основе изменений
        """
        print("🔄 Обновляем данные игроков...")
        
        # Загружаем текущие данные
        try:
            with open(self.players_file, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
        except FileNotFoundError:
            print("❌ Файл с данными игроков не найден. Сначала запусти userlist_parser.py")
            return False
        
        updated_count = 0
        
        for user_id, change_data in changes.items():
            if user_id in players_data:
                player = players_data[user_id]
                
                # Применяем изменения
                if 'credits' in player['data']:
                    player['data']['credits'] = max(0, player['data']['credits'] + change_data['credits'])
                
                if 'infection' in player['data']:
                    player['data']['infection'] = max(0, min(100, 
                        player['data']['infection'] + change_data['infection']))
                
                if 'whisper' in player['data']:
                    player['data']['whisper'] = max(-100, min(300,
                        player['data']['whisper'] + change_data['whisper']))
                
                # Обновляем время
                player['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                player['last_calculation'] = {
                    'credits_change': change_data['credits'],
                    'infection_change': change_data['infection'],
                    'whisper_change': change_data['whisper']
                }
                
                updated_count += 1
        
        # Сохраняем обновлённые данные
        with open(self.players_file, 'w', encoding='utf-8') as f:
            json.dump(players_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Обновлено {updated_count} игроков")
        return True
    
    def run_full_update(self):
        """
        Запускает полный цикл обновления
        """
        print("=" * 60)
        print("🔄 WHISPER OF THE VOID - ПОЛНОЕ ОБНОВЛЕНИЕ")
        print("=" * 60)
        
        start_time = time.time()
        
        # 1. Собираем актуальный список игроков
        print("\n1. 📥 Обновляем список игроков...")
        players_data = fetch_all_players()
        
        if not players_data:
            print("❌ Не удалось получить данные игроков. Прерывание.")
            return False
        
        # 2. Получаем свежие посты
        print("\n2. 📝 Анализируем активность...")
        recent_posts = self.get_recent_posts(hours=24)
        
        # 3. Анализируем активность
        user_activity = self.analyze_posts_for_stats(recent_posts)
        
        # 4. Рассчитываем изменения
        print("\n3. 🧮 Рассчитываем изменения показателей...")
        changes = self.calculate_daily_changes(players_data, user_activity)
        
        # 5. Обновляем данные
        print("\n4. 💾 Сохраняем обновлённые данные...")
        self.update_players_data(changes)
        
        # 6. Генерируем отчёт
        print("\n5. 📊 Генерируем отчёт...")
        self.generate_daily_report(players_data, user_activity, changes)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Общее время выполнения: {elapsed_time:.2f} секунд")
        print("🎉 Обновление завершено успешно!")
        
        return True
    
    def generate_daily_report(self, players_data, user_activity, changes):
        """Генерирует ежедневный отчёт"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_players': len(players_data),
            'active_players': len(user_activity),
            'top_contributors': [],
            'summary': {}
        }
        
        # Топ-3 самых активных
        active_users = sorted(
            user_activity.items(), 
            key=lambda x: x[1]['post_count'], 
            reverse=True
        )[:3]
        
        for user_id, activity in active_users:
            if str(user_id) in players_data:
                username = players_data[str(user_id)]['username']
                report['top_contributors'].append({
                    'username': username,
                    'posts': activity['post_count'],
                    'topics': activity['unique_topics']
                })
        
        # Сохраняем отчёт
        report_file = f"data/daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Отчёт сохранён: {report_file}")

# === ЗАПУСК ===
if __name__ == "__main__":
    core = WotVCore()
    
    # Запускаем полное обновление
    success = core.run_full_update()
    
    if success:
        print("\n✅ Система готова к работе!")
        print("\n📋 Что было сделано:")
        print("   1. 📥 Собран список игроков")
        print("   2. 📝 Проанализированы свежие посты")
        print("   3. 🧮 Рассчитаны изменения показателей")
        print("   4. 💾 Обновлены файлы данных")
        print("   5. 📊 Сгенерирован ежедневный отчёт")
        
        # Показываем текущие данные Void для проверки
        print("\n📊 Текущие данные Void (ID:2):")
        try:
            with open("data/players/2.json", 'r', encoding='utf-8') as f:
                void_data = json.load(f)
                print(f"   Кредиты: {void_data['data'].get('credits', 0)}")
                print(f"   Заражение: {void_data['data'].get('infection', 0)}%")
                print(f"   Шёпот: {void_data['data'].get('whisper', 0)}%")
        except FileNotFoundError:
            print("   Файл с данными Void не найден")
    else:
        print("\n❌ Обновление не удалось. Проверь логи выше.")
