"""
Парсер списка игроков для Whisper of the Void
Получает данные ВСЕХ игроков с одной страницы userlist.php
Интегрирован с GameCalculator для расчёта уровней и XP
"""

import requests
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup  # Удобная библиотека для парсинга HTML

# Импортируем GameCalculator, если он доступен
try:
    from game_calculator import GameCalculator
    CALCULATOR_AVAILABLE = True
    calculator = GameCalculator()
    print("✅ GameCalculator доступен для расчёта уровней")
except ImportError:
    CALCULATOR_AVAILABLE = False
    print("⚠️  GameCalculator не найден, уровни не будут рассчитаны")

def fetch_all_players():
    """
    Основная функция: загружает и парсит страницу со списком игроков.
    Возвращает словарь {user_id: данные_игрока}
    """
    url = "https://warframe.f-rpg.me/userlist.php"
    
    # Заголовки, чтобы выглядеть как браузер
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        print(f"📥 Загружаем список игроков...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Используем BeautifulSoup для удобного парсинга HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим таблицу с пользователями
        user_table = soup.find('table', summary="Пользователи, отфильтрованные по критерию.")
        
        if not user_table:
            print("❌ Таблица пользователей не найдена!")
            # Сохраним HTML для отладки
            with open('debug_userlist.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            return {}
        
        # Собираем всех игроков
        players = {}
        
        # Проходим по всем строкам таблицы (кроме заголовка)
        for row in user_table.find_all('tr')[1:]:  # Пропускаем заголовок <thead>
            cols = row.find_all('td')
            if len(cols) < 6:  # Нужно минимум 6 столбцов
                continue
            
            # 1. Извлекаем ID пользователя из ссылки на профиль
            profile_link = cols[0].find('a', href=True)
            if profile_link:
                href = profile_link['href']
                # Извлекаем ID из ссылки вида /profile.php?id=2
                user_id_match = re.search(r'id=(\d+)', href)
                user_id = int(user_id_match.group(1)) if user_id_match else None
            else:
                user_id = None
            
            # 2. Имя пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ
            username_elem = cols[0].find('span', class_='usersname')
            if username_elem:
                # Внутри <span class="usersname"> есть ссылка <a>
                username_link = username_elem.find('a')
                username = username_link.text.strip() if username_link else username_elem.text.strip()
            else:
                # Резервный вариант: ищем любую ссылку в первом столбце
                username_link = cols[0].find('a')
                username = username_link.text.strip() if username_link else "Неизвестно"
            
            # 3. СТАТУС - самый важный столбец!
            status_text = cols[1].text.strip()  # Второй столбец: "К:+200 З:+13% Ш:+312%"
            
            # 4. Дополнительные данные
            posts = cols[3].text.strip()  # Количество сообщений
            registered = cols[4].text.strip()  # Дата регистрации
            last_visit = cols[5].text.strip()  # Последний визит
            
            if user_id and status_text:
                # Парсим статус: К:+200 З:+13% Ш:+312%
                data = parse_status(status_text)
                
                # Формируем полную запись игрока
                player_entry = {
                    'user_id': user_id,
                    'username': username,
                    'status_raw': status_text,
                    'data': data,
                    'forum_stats': {
                        'posts': int(posts) if posts.isdigit() else 0,
                        'registered': registered,
                        'last_visit': last_visit
                    },
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Рассчитываем уровень и XP, если доступен калькулятор
                if CALCULATOR_AVAILABLE:
                    try:
                        calculate_player_level(player_entry)
                    except Exception as e:
                        print(f"   ⚠️  Ошибка расчёта уровня для {username}: {e}")
                
                players[user_id] = player_entry
                
                # Выводим информацию с уровнем, если рассчитан
                if 'level' in player_entry['data']:
                    print(f"   👤 {username} (ID:{user_id}): Ур.{player_entry['data']['level']} - {status_text}")
                else:
                    print(f"   👤 {username} (ID:{user_id}): {status_text}")
        
        print(f"\n✅ Успешно! Найдено игроков: {len(players)}")
        return players
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return {}

def parse_status(status_text):
    """
    Парсит строку статуса в формате "К:+200 З:+13% Ш:+312%"
    Возвращает словарь с числовыми значениями
    """
    result = {}
    
    # Универсальные регулярки для поиска значений
    patterns = {
        'credits': r'К:\s*([+-]?\d+)',
        'infection': r'З:\s*([+-]?\d+)%?',  # % может быть или не быть
        'whisper': r'Ш:\s*([+-]?\d+)%?',
    }
    
    # Альтернативные названия (на всякий случай)
    alt_patterns = {
        'credits': [r'credits?:\s*([+-]?\d+)', r'кредит[ы\w]*:\s*([+-]?\d+)'],
        'infection': [r'заражен\w*:\s*([+-]?\d+)%?', r'inf(ection)?:\s*([+-]?\d+)%?'],
        'whisper': [r'ш[её]пот\w*:\s*([+-]?\d+)%?', r'whisper:\s*([+-]?\d+)%?'],
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, status_text, re.IGNORECASE)
        if match:
            result[key] = int(match.group(1))
        else:
            # Пробуем альтернативные паттерны
            for alt_pattern in alt_patterns.get(key, []):
                match = re.search(alt_pattern, status_text, re.IGNORECASE)
                if match:
                    result[key] = int(match.group(1) if match.group(1) else match.group(2))
                    break
    
    return result

def calculate_player_level(player_data):
    """
    Рассчитывает уровень игрока и XP на основе текущих статистик
    с использованием GameCalculator
    """
    if not CALCULATOR_AVAILABLE:
        return
    
    try:
        data = player_data['data']
        
        # Получаем значения статистик
        credits = data.get('credits', 0)
        infection = data.get('infection', 0)
        whisper = data.get('whisper', 0)
        
        # Рассчитываем XP
        xp = calculator.calculate_xp(
            credits=credits,
            infection=infection,
            whisper=whisper,
            days_since_reg=30,  # Значение по умолчанию
            activity_multiplier=1.0  # Без активности при парсинге
        )
        
        # Рассчитываем уровень на основе XP
        level = 1
        max_level = 100  # Максимальный уровень из GameCalculator
        
        for lvl in range(1, max_level + 1):
            level_info = calculator.get_level_info(lvl)
            if xp >= level_info['xp_required']:
                level = lvl
            else:
                break
        
        # Получаем информацию о текущем уровне
        level_info = calculator.get_level_info(level)
        
        # Сохраняем расчёты в данных игрока
        data['xp'] = xp
        data['level'] = level
        data['xp_to_next_level'] = level_info['xp_required'] - xp
        
        # Добавляем информацию о текущем уровне
        data['level_info'] = {
            'current_level': level,
            'xp': xp,
            'xp_required': level_info['xp_required'],
            'bonus_credits': level_info['bonus_credits'],
            'infection_resistance': level_info['infection_resistance'],
            'whisper_bonus': level_info['whisper_bonus']
        }
        
    except Exception as e:
        print(f"❌ Ошибка при расчёте уровня для {player_data['username']}: {e}")

def save_players_data(players_data, output_dir="data/players"):
    """
    Сохраняет данные игроков в JSON файлы.
    Каждый игрок -> отдельный файл user_id.json
    Также создаёт общий файл со всеми игроками.
    """
    import os
    
    # Создаём папку, если её нет
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Сохраняем каждого игрока в отдельный файл
    for user_id, data in players_data.items():
        filename = os.path.join(output_dir, f"{user_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 2. Сохраняем общий файл со всеми игроками
    all_players_file = os.path.join(output_dir, "all_players.json")
    with open(all_players_file, 'w', encoding='utf-8') as f:
        json.dump(players_data, f, ensure_ascii=False, indent=2)
    
    # 3. Сохраняем упрощённую версию для веб-интерфейса
    simple_data = {}
    for user_id, data in players_data.items():
        player_simple = {
            'username': data['username'],
            'credits': data['data'].get('credits', 0),
            'infection': data['data'].get('infection', 0),
            'whisper': data['data'].get('whisper', 0),
            'last_visit': data['forum_stats']['last_visit']
        }
        
        # Добавляем информацию об уровне, если она есть
        if 'level' in data['data']:
            player_simple.update({
                'level': data['data']['level'],
                'xp': data['data'].get('xp', 0),
                'xp_to_next_level': data['data'].get('xp_to_next_level', 0)
            })
        
        simple_data[user_id] = player_simple
    
    web_data_file = "players_data.json"  # Будет создан в корне
    with open(web_data_file, 'w', encoding='utf-8') as f:
        json.dump(simple_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Данные сохранены:")
    print(f"   - {len(players_data)} файлов в {output_dir}/")
    print(f"   - Общий файл: {output_dir}/all_players.json")
    print(f"   - Веб-версия: players_data.json")
    
    return len(players_data)

def generate_stats_report(players_data):
    """Генерирует простой отчёт по статистике игроков."""
    if not players_data:
        return
    
    print("\n📊 СТАТИСТИКА ИГРОКОВ:")
    print("=" * 50)
    
    # Считаем средние значения
    credits_list = [p['data'].get('credits', 0) for p in players_data.values()]
    infection_list = [p['data'].get('infection', 0) for p in players_data.values()]
    whisper_list = [p['data'].get('whisper', 0) for p in players_data.values()]
    
    if credits_list:
        print(f"💰 Кредиты: {min(credits_list)} ← {sum(credits_list)/len(credits_list):.0f} → {max(credits_list)}")
    if infection_list:
        print(f"🦠 Заражение: {min(infection_list)}% ← {sum(infection_list)/len(infection_list):.0f}% → {max(infection_list)}%")
    if whisper_list:
        print(f"👁️ Шёпот: {min(whisper_list)}% ← {sum(whisper_list)/len(whisper_list):.0f}% → {max(whisper_list)}%")
    
    # Статистика по уровням, если есть
    if CALCULATOR_AVAILABLE and any('level' in p['data'] for p in players_data.values()):
        levels = [p['data'].get('level', 1) for p in players_data.values() if 'level' in p['data']]
        xp_values = [p['data'].get('xp', 0) for p in players_data.values() if 'xp' in p['data']]
        
        if levels:
            print(f"🎮 Уровни: {min(levels)} ← {sum(levels)/len(levels):.1f} → {max(levels)}")
        if xp_values:
            avg_xp = sum(xp_values)/len(xp_values)
            print(f"⭐ Средний XP: {avg_xp:,.0f}")
    
    # Самые активные игроки
    print(f"\n👥 Всего игроков: {len(players_data)}")
    
    # Топ-3 по кредитам
    top_credits = sorted(players_data.items(), 
                        key=lambda x: x[1]['data'].get('credits', 0), 
                        reverse=True)[:3]
    
    print(f"\n🏆 Топ-3 по кредитам:")
    for user_id, data in top_credits:
        level_info = f" (Ур.{data['data'].get('level', '?')})" if 'level' in data['data'] else ""
        print(f"   {data['username']}{level_info}: {data['data'].get('credits', 0):,} кредитов")
    
    # Топ-3 по уровню, если есть уровни
    if CALCULATOR_AVAILABLE and any('level' in p['data'] for p in players_data.values()):
        top_levels = sorted(players_data.items(),
                          key=lambda x: x[1]['data'].get('level', 0),
                          reverse=True)[:3]
        
        print(f"\n🏅 Топ-3 по уровню:")
        for user_id, data in top_levels:
            if 'level' in data['data']:
                level = data['data']['level']
                xp = data['data'].get('xp', 0)
                next_level_xp = data['data'].get('xp_to_next_level', 0)
                print(f"   {data['username']}: Ур.{level} (XP: {xp:,}, до след.: {next_level_xp:,})")

# === ЗАПУСК ПАРСЕРА ===
if __name__ == "__main__":
    print("=" * 60)
    print("🎮 WHISPER OF THE VOID - ПАРСЕР СПИСКА ИГРОКОВ")
    if CALCULATOR_AVAILABLE:
        print("🎯 Интегрирован с GameCalculator")
    print("=" * 60)
    
    # Запускаем парсинг
    start_time = time.time()
    players = fetch_all_players()
    
    if players:
        # Сохраняем данные
        save_players_data(players)
        
        # Генерируем отчёт
        generate_stats_report(players)
        
        # Показываем пример данных
        print(f"\n📄 Пример данных Void (ID:2):")
        if 2 in players:
            void_data = players[2]
            print(f"   Имя: {void_data['username']}")
            print(f"   Статус: {void_data['status_raw']}")
            
            if 'level' in void_data['data']:
                level_data = void_data['data']['level_info']
                print(f"   Уровень: {level_data['current_level']} (XP: {void_data['data']['xp']:,})")
                print(f"   До след. уровня: {void_data['data']['xp_to_next_level']:,} XP")
            
            print(f"   Данные: Кредиты={void_data['data'].get('credits', 0)}, "
                  f"Заражение={void_data['data'].get('infection', 0)}%, "
                  f"Шёпот={void_data['data'].get('whisper', 0)}%")
            print(f"   Сообщений: {void_data['forum_stats']['posts']}")
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Время выполнения: {elapsed_time:.2f} секунд")
        print(f"🎯 Парсинг успешно завершён!")
        
    else:
        print("😞 Не удалось получить данные игроков.")
        print("\nВозможные причины:")
        print("1. Изменилась структура страницы userlist.php")
        print("2. Проблемы с подключением к форуму")
        print("3. Форум временно недоступен")
