"""
Модуль для расчета игровых показателей Whisper of the Void
Содержит формулы для кредитов, заражения и шёпота
"""

import time
from datetime import datetime, timedelta

class GameCalculator:
    def __init__(self, base_credits=0, base_infection=0, base_whisper=0):
        """Инициализация калькулятора с базовыми значениями"""
        self.base_credits = base_credits
        self.base_infection = base_infection
        self.base_whisper = base_whisper
        
    def calculate_daily_income(self, player_data, activity_data):
        """
        Рассчитывает ежедневный доход игрока
        
        Формула:
        - Базовый доход: 10 кредитов
        - За каждый пост: +5 кредитов
        - За уникальную тему: +10 кредитов
        - Бонус активности (если > 5 постов): +20 кредитов
        """
        credits = 10  # Базовый ежедневный доход
        
        # Бонусы за активность
        if activity_data:
            posts = activity_data.get('post_count', 0)
            unique_topics = activity_data.get('unique_topics', 0)
            
            credits += posts * 5  # +5 за каждый пост
            credits += unique_topics * 10  # +10 за каждую уникальную тему
            
            # Бонус за высокую активность
            if posts >= 5:
                credits += 20
                
        return credits
    
    def calculate_infection_progression(self, player_data, activity_data, days_since_registration):
        """
        Рассчитывает прогрессию заражения
        
        Формула:
        - Базовое заражение: +0.5% в день
        - За каждый пост: -0.1% (активность замедляет заражение)
        - Если шёпот > 50: +0.2% в день
        - Если последний визит > 7 дней: +1% в день (стагнация)
        """
        infection = 0.5  # Базовое ежедневное заражение
        
        # Модификаторы активности
        if activity_data:
            posts = activity_data.get('post_count', 0)
            infection -= posts * 0.1  # Активность замедляет заражение
            
        # Модификатор шёпота
        current_whisper = player_data.get('whisper', 0)
        if current_whisper > 50:
            infection += 0.2
            
        # Модификатор неактивности
        last_visit = player_data.get('last_visit', '')
        if self._is_inactive(last_visit):
            infection += 1.0
            
        # Ограничиваем значение
        infection = max(0.1, min(2.0, infection))
        
        return infection
    
    def calculate_whisper_influence(self, player_data, activity_data, current_infection):
        """
        Рассчитывает влияние Шёпота Бездны
        
        Формула:
        - Базовое влияние: ±0% (нейтрально)
        - За каждые 10% заражения: +0.5%
        - За каждый пост в уникальной теме: +1%
        - Если инфекция > 70: +2% (критический уровень)
        """
        whisper = 0  # Базовое влияние
        
        # Влияние заражения
        whisper += (current_infection / 10) * 0.5
        
        # Влияние активности
        if activity_data:
            unique_topics = activity_data.get('unique_topics', 0)
            whisper += unique_topics * 1
            
        # Критический уровень заражения
        if current_infection > 70:
            whisper += 2
            
        # Случайный фактор (10% шанс на ±1-3%)
        import random
        if random.random() < 0.1:
            whisper += random.choice([-3, -2, -1, 1, 2, 3])
            
        return whisper
    
    def calculate_status_bonuses(self, status_text):
        """
        Извлекает бонусы из статуса пользователя
        
        Формуты статуса:
        - К:+200 (кредиты)
        - З:+13% (заражение)
        - Ш:+312% (шёпот)
        """
        bonuses = {
            'credits_bonus': 0,
            'infection_bonus': 0,
            'whisper_bonus': 0
        }
        
        try:
            import re
            
            # Поиск кредитов
            credits_match = re.search(r'К:\s*([+-]?\d+)', status_text)
            if credits_match:
                bonuses['credits_bonus'] = int(credits_match.group(1))
                
            # Поиск заражения
            infection_match = re.search(r'З:\s*([+-]?\d+)%?', status_text)
            if infection_match:
                bonuses['infection_bonus'] = int(infection_match.group(1))
                
            # Поиск шёпота
            whisper_match = re.search(r'Ш:\s*([+-]?\d+)%?', status_text)
            if whisper_match:
                bonuses['whisper_bonus'] = int(whisper_match.group(1))
                
        except Exception as e:
            print(f"Ошибка парсинга статуса: {e}")
            
        return bonuses
    
    def calculate_player_progression(self, player_data, activity_data, days_since_registration):
        """
        Основная функция расчета прогрессии игрока
        Возвращает обновленные данные игрока
        """
        # Получаем текущие значения
        current_credits = player_data.get('credits', 0)
        current_infection = player_data.get('infection', 0)
        current_whisper = player_data.get('whisper', 0)
        
        # Рассчитываем изменения
        daily_income = self.calculate_daily_income(player_data, activity_data)
        infection_change = self.calculate_infection_progression(player_data, activity_data, days_since_registration)
        whisper_change = self.calculate_whisper_influence(player_data, activity_data, current_infection)
        
        # Получаем бонусы из статуса
        status_text = player_data.get('status_raw', '')
        status_bonuses = self.calculate_status_bonuses(status_text)
        
        # Применяем изменения с ограничениями
        new_credits = current_credits + daily_income + status_bonuses['credits_bonus']
        new_infection = current_infection + infection_change + status_bonuses['infection_bonus']
        new_whisper = current_whisper + whisper_change + status_bonuses['whisper_bonus']
        
        # Ограничиваем значения
        new_infection = max(0, min(100, new_infection))
        new_whisper = max(-100, min(500, new_whisper))
        
        # Формируем результат
        result = {
            'credits': round(new_credits),
            'infection': round(new_infection, 1),
            'whisper': round(new_whisper, 1),
            'changes': {
                'credits_change': round(daily_income),
                'infection_change': round(infection_change, 1),
                'whisper_change': round(whisper_change, 1),
                'status_bonuses': status_bonuses
            }
        }
        
        return result
    
    def _is_inactive(self, last_visit_str, days_threshold=7):
        """Проверяет, является ли игрок неактивным"""
        try:
            # Пытаемся распарсить дату последнего визита
            # Это упрощенная реализация - нужно адаптировать под ваш формат дат
            today = datetime.now()
            
            # Если последний визит "Сегодня" или содержит дату
            if "Сегодня" in last_visit_str:
                return False
                
            # Пытаемся распарсить дату формата YYYY-MM-DD
            import re
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', last_visit_str)
            if date_match:
                year, month, day = map(int, date_match.groups())
                last_visit = datetime(year, month, day)
                days_diff = (today - last_visit).days
                return days_diff > days_threshold
                
        except Exception:
            pass
            
        return False

# Пример использования
if __name__ == "__main__":
    # Тестовые данные
    test_player = {
        'credits': 100,
        'infection': 13,
        'whisper': 50,
        'status_raw': 'К:+200 З:+13% Ш:+312%',
        'last_visit': 'Сегодня'
    }
    
    test_activity = {
        'post_count': 3,
        'unique_topics': 2
    }
    
    # Создаем калькулятор и рассчитываем
    calculator = GameCalculator()
    result = calculator.calculate_player_progression(
        test_player, 
        test_activity, 
        days_since_registration=30
    )
    
    print("Результаты расчета:")
    print(f"Кредиты: {test_player['credits']} → {result['credits']}")
    print(f"Заражение: {test_player['infection']}% → {result['infection']}%")
    print(f"Шёпот: {test_player['whisper']}% → {result['whisper']}%")
    print(f"\nИзменения: {result['changes']}")
