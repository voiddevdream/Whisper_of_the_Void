"""
ЯДРО Whisper of the Void
Объединяет парсинг списка игроков и постов через API
"""

import requests
import json
import time
import os
from datetime import datetime

# Импортируем функцию из нашего парсера
try:
    from userlist_parser import fetch_all_players, save_players_data
except ImportError:
    # Если не удалось импортировать, создадим заглушки
    def fetch_all_players():
        print("❌ Ошибка: не удалось импортировать userlist_parser")
        return {}
    
    def save_players_data(players_data, output_dir="data/players"):
        """Переопределенная функция, чтобы гарантировать создание players_data.json в корне"""
        print("⚠️  Используется заглушка save_players_data. Данные не сохранены.")
        # Создаем упрощённую версию для веб-интерфейса и сохраняем в корень
        simple_data = {
            user_id: {
                'username': data['username'],
                'credits': data['data'].get('credits', 0),
                'infection': data['data'].get('infection', 0),
                'whisper': data['data'].get('whisper', 0),
                'last_visit': data['forum_stats']['last_visit']
            }
            for user_id, data in players_data.items()
        }
        with open('players_data.json', 'w', encoding='utf-8') as f:
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Упрощенные данные сохранены в players_data.json")
        return len(players_data)


class WotVCore:
    def __init__(self):
        self.api_url = "https://warframe.f-rpg.me/api.php"
        self.players_file = "data/players/all_players.json"
        self.posts_file = "data/latest_posts.json"
        
    def get_recent_posts(self, hours=24):
        """
        Получает свежие посты за последние N часов через API
        Сейчас работает с конкретной темой (ID=8 - тестовая)
        """
        print(f"📝 Получаем посты за последние {hours} часов...")
        
        # Рассчитываем timestamp для фильтрации
        cutoff_time = int(time.time()) - (hours * 3600)
        
        # Параметры API запроса - УКАЗЫВАЕМ КОНКРЕТНУЮ ТЕМУ
        params = {
            'method': 'post.get',
            'topic_id': 8,  # Тестовая тема ID=8
            'limit': 50,
            'sort_by': 'id',
            'sort_dir': 'desc'
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                if 'response' in data:
                    posts = data['response']
                    
                    if isinstance(posts, list) and posts:
                        # Фильтруем по времени
                        recent_posts = []
                        for post in posts:
                            post_time = int(post.get('posted', 0))
                            if post_time > cutoff_time:
                                recent_posts.append(post)
                        
                        print(f"✅ Найдено {len(recent_posts)} новых постов (всего {len(posts)})")
                        
                        # Показываем пример для отладки
                        if recent_posts:
                            print(f"   Пример: {recent_posts[0]['username']} - '{recent_posts[0]['message'][:50]}...'")
                        
                        return recent_posts
                    else:
                        print(f"⚠️  Постов не найдено или ответ не список")
                        return []
                else:
                    print(f"⚠️  В ответе API нет 'response'")
                    # Сохраним ответ для отладки
                    print(f"   Ответ API: {json.dumps(data, indent=2)[:200]}...")
                    return []
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"   Текст ответа: {response.text[:100]}...")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка при получении постов: {e}")
            return []
    
    def analyze_posts_for_stats(self, posts):
        """
        Анализирует посты для обновления статистики игроков
        """
        if not posts:
            print("📊 Нет постов для анализа")
            return {}
        
        print("📊 Анализируем активность в постах...")
        
        # Считаем посты по игрокам
        user_activity = {}
        
        for post in posts:
            user_id = post.get('user_id')
            if not user_id:
                continue
            
            try:
                user_id = int(user_id)
            except ValueError:
                continue
            
            if user_id not in user_activity:
                user_activity[user_id] = {
                    'post_count': 0,
                    'last_post': post.get('posted'),
                    'topics': set()
                }
            
            user_activity[user_id]['post_count'] += 1
            topic_id = post.get('topic_id')
            if topic_id:
                user_activity[user_id]['topics'].add(topic_id)
        
        # Преобразуем в удобный формат
        for user_id, data in user_activity.items():
            data['unique_topics'] = len(data['topics'])
            # Удаляем set, он не сериализуется в JSON
            data.pop('topics', None)
        
        print(f"📈 Активность {len(user_activity)} игроков")
        for user_id, activity in user_activity.items():
            print(f"   👤 ID:{user_id}: {activity['post_count']} постов")
        
        return user_activity
    
    def calculate_daily_changes(self, players_data, user_activity):
        """
        Рассчитывает ежедневные изменения показателей
        Базовые изменения применяются ВСЕМ игрокам
        """
        print("🧮 Рассчитываем ежедневные изменения...")
        
        changes = {}
        
        for user_id_str, player_data in players_data.items():
            try:
                user_id_int = int(user_id_str)
            except ValueError:
                continue
            
            activity = user_activity.get(user_id_int, {})
            
            # БАЗОВЫЕ изменения для ВСЕХ игроков
            daily_changes = {
                'credits': 5,  # Базовый доход
                'infection': 0.2,  # Базовый рост заражения в день
                'whisper': 0
            }
            
            # Бонусы за активность
            if activity.get('post_count', 0) > 0:
                # За каждый пост +10 кредитов
                daily_changes['credits'] += activity.get('post_count', 0) * 10
                
                # За каждый уникальный топик +3% к шёпоту
                daily_changes['whisper'] += activity.get('unique_topics', 0) * 3
                
                # Активные игроки медленнее заражаются
                infection_reduction = min(0.15, activity.get('post_count', 0) * 0.03)
                daily_changes['infection'] -= infection_reduction
            
            changes[user_id_str] = daily_changes
            
            # Отладочная информация
            if activity:
                print(f"   👤 {player_data.get('username', f'ID:{user_id_str}')}: "
                      f"+{daily_changes['credits']}💰, "
                      f"{'+' if daily_changes['infection'] >= 0 else ''}{daily_changes['infection']:.2f}%🦠, "
                      f"{'+' if daily_changes['whisper'] >= 0 else ''}{daily_changes['whisper']}%👁️")
        
        return changes
    
    def update_players_data(self, players_data, changes):
        """
        Обновляет данные игроков на основе изменений
        """
        print("🔄 Обновляем данные игроков...")
        
        updated_count = 0
        
        for user_id, player in players_data.items():
            if user_id in changes:
                change_data = changes[user_id]
                
                # Применяем изменения к данным игрока
                if 'credits' in player['data']:
                    player['data']['credits'] = player['data'].get('credits', 0) + change_data['credits']
                
                if 'infection' in player['data']:
                    new_infection = player['data'].get('infection', 0) + change_data['infection']
                    # Ограничиваем от 0 до 100%
                    player['data']['infection'] = max(0, min(100, new_infection))
                
                if 'whisper' in player['data']:
                    new_whisper = player['data'].get('whisper', 0) + change_data['whisper']
                    # Ограничиваем от -100 до 300%
                    player['data']['whisper'] = max(-100, min(300, new_whisper))
                
                # Обновляем время
                player['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                player['last_calculation'] = {
                    'credits_change': change_data['credits'],
                    'infection_change': change_data['infection'],
                    'whisper_change': change_data['whisper'],
                    'calculation_time': datetime.now().isoformat()
                }
                
                updated_count += 1
        
        # Сохраняем обновлённые данные
        save_players_data(players_data)
        
        print(f"✅ Обновлено {updated_count} игроков")
        return updated_count
    
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
        
        print(f"   Найдено {len(players_data)} игроков")
        
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
        updated_count = self.update_players_data(players_data, changes)
        
        # 6. Генерируем отчёт
        print("\n5. 📊 Генерируем отчёт...")
        self.generate_daily_report(players_data, user_activity, changes)
        
        elapsed_time = time.time() - start_time
        
        # 7. Показываем итоги
        print("\n" + "=" * 60)
        print("🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
        print("=" * 60)
        print(f"📊 Итоги:")
        print(f"   👥 Игроков обработано: {len(players_data)}")
        print(f"   ✍️  Активных игроков: {len(user_activity)}")
        print(f"   🔄 Обновлено записей: {updated_count}")
        print(f"   ⏱️  Время выполнения: {elapsed_time:.2f} секунд")
        
        # Показываем текущие данные Void для проверки
        print(f"\n📊 Текущие данные Void (ID:2):")
        if '2' in players_data:
            void_data = players_data['2']
            print(f"   Имя: {void_data['username']}")
            print(f"   Кредиты: {void_data['data'].get('credits', 0)} (+{changes.get('2', {}).get('credits', 0)})")
            print(f"   Заражение: {void_data['data'].get('infection', 0):.1f}% (+{changes.get('2', {}).get('infection', 0):.2f})")
            print(f"   Шёпот: {void_data['data'].get('whisper', 0)}% (+{changes.get('2', {}).get('whisper', 0)})")
        
        return True
    
    def generate_daily_report(self, players_data, user_activity, changes):
        """Генерирует ежедневный отчёт"""
        from datetime import datetime
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'total_players': len(players_data),
            'active_players': len(user_activity),
            'top_contributors': [],
            'summary': {
                'total_credits_added': sum(c.get('credits', 0) for c in changes.values()),
                'total_infection_change': sum(c.get('infection', 0) for c in changes.values()),
                'total_whisper_change': sum(c.get('whisper', 0) for c in changes.values())
            }
        }
        
        # Топ-3 самых активных
        if user_activity:
            active_users = sorted(
                user_activity.items(), 
                key=lambda x: x[1]['post_count'], 
                reverse=True
            )[:3]
            
            for user_id, activity in active_users:
                user_id_str = str(user_id)
                if user_id_str in players_data:
                    player = players_data[user_id_str]
                    report['top_contributors'].append({
                        'user_id': user_id,
                        'username': player['username'],
                        'posts': activity['post_count'],
                        'topics': activity['unique_topics'],
                        'credits_earned': changes.get(user_id_str, {}).get('credits', 0)
                    })
        
        # Сохраняем отчёт
        import os
        os.makedirs('data', exist_ok=True)
        report_file = f"data/daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Отчёт сохранён: {report_file}")
        
        # Краткий вывод отчёта
        print(f"   📅 Дата: {report['date']}")
        print(f"   👥 Всего игроков: {report['total_players']}")
        print(f"   ✍️  Активных: {report['active_players']}")
        if report['top_contributors']:
            print(f"   🏆 Топ активных: {', '.join(p['username'] for p in report['top_contributors'])}")


# === ЗАПУСК ===
if __name__ == "__main__":
    print("🎮 Запуск ядра Whisper of the Void...")
    print("=" * 60)
    
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
    else:
        print("\n❌ Обновление не удалось. Проверь логи выше.")
