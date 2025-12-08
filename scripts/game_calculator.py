"""
Модуль игровых расчетов для Whisper of the Void
Содержит формулы для прогрессии, заражения, шёпота и т.д.
"""

import math

class GameCalculator:
    """Калькулятор игровых формул с системой уровней и ограничениями отображения"""
    
    def __init__(self):
        # Константы баланса
        self.BASE_CREDITS = 5
        self.BASE_INFECTION = 0.2
        self.CREDITS_PER_POST = 10
        self.WHISPER_PER_TOPIC = 3
        self.INFECTION_REDUCTION_PER_POST = 0.03
        
        # Система уровней
        self.BASE_XP_PER_LEVEL = 1000
        self.LEVEL_EXPONENT = 1.8
        self.MAX_DISPLAY_INFECTION = 100  # Максимальное отображаемое значение заражения
        self.MAX_DISPLAY_WHISPER = 100    # Максимальное отображаемое значение шёпота
        
    def calculate_player_progression(self, player_data, activity, days_since_reg=30):
        """
        Основной метод расчета прогрессии игрока
        
        Args:
            player_data (dict): Данные игрока из userlist_parser
            activity (dict): Активность {'post_count': X, 'unique_topics': Y}
            days_since_reg (int): Дней с регистрации
        
        Returns:
            dict: Новые значения и изменения
        """
        post_count = activity.get('post_count', 0)
        unique_topics = activity.get('unique_topics', 0)
        
        # 1. Расчет изменения кредитов
        credits_change = self.BASE_CREDITS + (post_count * self.CREDITS_PER_POST)
        
        # 2. Расчет заражения (учитываем активность)
        infection_change = self.BASE_INFECTION
        if post_count > 0:
            infection_change -= min(0.15, post_count * self.INFECTION_REDUCTION_PER_POST)
        
        # 3. Расчет шёпота (за уникальные темы)
        whisper_change = unique_topics * self.WHISPER_PER_TOPIC
        
        # 4. Получаем текущие значения
        current_credits = player_data['data'].get('credits', 0)
        current_infection = player_data['data'].get('infection', 0)
        current_whisper = player_data['data'].get('whisper', 0)
        
        # 5. Рассчитываем новые значения (без ограничений для реального хранения)
        new_infection = current_infection + infection_change
        new_whisper = current_whisper + whisper_change
        
        # 6. Рассчитываем XP и уровень
        xp = self.calculate_xp(current_credits, current_infection, current_whisper, days_since_reg, post_count)
        level = self.calculate_level_from_xp(xp)
        
        # 7. Получаем информацию об уровне
        level_info = self.get_level_info(level)
        next_level_info = self.get_level_info(level + 1)
        xp_to_next = next_level_info['xp_required'] - xp if level < 100 else 0
        
        return {
            'current': {
                'credits': current_credits + credits_change,
                'infection': new_infection,  # Реальное значение (может быть > 100)
                'whisper': new_whisper,      # Реальное значение (может быть > 100)
                'display_infection': min(new_infection, self.MAX_DISPLAY_INFECTION),
                'display_whisper': min(new_whisper, self.MAX_DISPLAY_WHISPER),
                'xp': xp,
                'level': level
            },
            'changes': {
                'credits_change': credits_change,
                'infection_change': infection_change,
                'whisper_change': whisper_change,
                'posts_used': post_count,
                'topics_used': unique_topics
            },
            'progression': {
                'xp_to_next_level': xp_to_next,
                'current_level_info': level_info,
                'next_level_info': next_level_info if level < 100 else None,
                'has_exceeded_infection': new_infection > self.MAX_DISPLAY_INFECTION,
                'has_exceeded_whisper': new_whisper > self.MAX_DISPLAY_WHISPER,
                'real_infection': new_infection,
                'real_whisper': new_whisper
            }
        }
    
    def calculate_xp(self, credits, infection, whisper, days_since_reg=30, post_count=0):
        """
        Рассчитывает XP игрока на основе его статистик
        """
        # Используем display значения для расчёта XP (максимум 100)
        display_infection = min(infection, self.MAX_DISPLAY_INFECTION)
        display_whisper = min(whisper, self.MAX_DISPLAY_WHISPER)
        
        # Базовый XP от кредитов (1 кредит = 1 XP)
        xp_from_credits = credits * 1.0
        
        # XP от заражения
        xp_from_infection = display_infection * 10 * (1.0 + display_infection / 100)
        
        # XP от шёпота
        xp_from_whisper = display_whisper * 25 * (1.0 + abs(display_whisper) / 100)
        
        # XP от активности
        activity_multiplier = 1.0 + (post_count * 0.1)
        xp_from_activity = days_since_reg * 50 * activity_multiplier
        
        # Итоговый XP (взвешенная сумма)
        total_xp = (
            xp_from_credits * 0.3 +
            xp_from_infection * 0.2 +
            xp_from_whisper * 0.4 +
            xp_from_activity * 0.1
        )
        
        return int(total_xp)
    
    def calculate_level_from_xp(self, xp):
        """
        Рассчитывает уровень игрока на основе XP
        """
        level = 1
        for lvl in range(1, 101):  # До 100 уровней
            level_info = self.get_level_info(lvl)
            if xp >= level_info['xp_required']:
                level = lvl
            else:
                break
        return level
    
    def get_level_info(self, level):
        """
        Возвращает информацию о конкретном уровне
        """
        if level < 1:
            level = 1
            
        # XP требуется для достижения этого уровня
        xp_required = int(self.BASE_XP_PER_LEVEL * math.pow(level, self.LEVEL_EXPONENT))
        
        # Бонусы за уровень
        bonus_credits = level * 5
        infection_resistance = min(level * 0.5, 30)
        whisper_bonus = level * 2
        
        return {
            'level': level,
            'xp_required': xp_required,
            'bonus_credits': bonus_credits,
            'infection_resistance': infection_resistance,
            'whisper_bonus': whisper_bonus
        }
    
    def get_display_values(self, infection, whisper):
        """
        Возвращает значения для отображения (с ограничением до 100%)
        """
        return {
            'display_infection': min(infection, self.MAX_DISPLAY_INFECTION),
            'display_whisper': min(whisper, self.MAX_DISPLAY_WHISPER),
            'has_exceeded_infection': infection > self.MAX_DISPLAY_INFECTION,
            'has_exceeded_whisper': whisper > self.MAX_DISPLAY_WHISPER,
            'real_infection': infection,
            'real_whisper': whisper
        }
    
    def calculate_infection_risk(self, current_infection, whisper_level):
        """
        Рассчитывает риск событий на основе заражения и шёпота
        Использует display значения
        """
        display_infection = min(current_infection, self.MAX_DISPLAY_INFECTION)
        display_whisper = min(whisper_level, self.MAX_DISPLAY_WHISPER)
        
        if display_infection >= 100:
            return {
                'status': 'Требуется превращение',
                'level': 'critical',
                'real_value': current_infection
            }
        elif display_infection >= 80:
            return {
                'status': 'Высокий риск',
                'level': 'high',
                'real_value': current_infection
            }
        elif display_whisper >= 150:
            return {
                'status': 'Влияние Бездны',
                'level': 'whisper',
                'real_value': whisper_level
            }
        elif current_infection > self.MAX_DISPLAY_INFECTION or whisper_level > self.MAX_DISPLAY_WHISPER:
            return {
                'status': 'Запредельные значения',
                'level': 'exceeded',
                'real_infection': current_infection,
                'real_whisper': whisper_level
            }
        else:
            return {
                'status': 'Стабильно',
                'level': 'stable',
                'real_value': current_infection
            }
    
    def calculate_infection_consequences(self, infection_level):
        """
        Рассчитывает последствия высокого уровня заражения
        """
        display_infection = min(infection_level, self.MAX_DISPLAY_INFECTION)
        
        consequences = []
        
        if infection_level > self.MAX_DISPLAY_INFECTION:
            consequences.append({
                'type': 'exceeded',
                'message': f'Заражение превысило {self.MAX_DISPLAY_INFECTION}% (реальное: {infection_level:.1f}%)',
                'effect': 'Скрытые мутации'
            })
        
        if display_infection >= 100:
            consequences.append({
                'type': 'transformation',
                'message': 'Полное превращение в Техноцит',
                'effect': 'Игрок становится NPC'
            })
        elif display_infection >= 80:
            consequences.append({
                'type': 'mutation',
                'message': 'Критический уровень заражения',
                'effect': '-30% к сопротивлению'
            })
        elif display_infection >= 50:
            consequences.append({
                'type': 'symptoms',
                'message': 'Заметные симптомы',
                'effect': '-15% к эффективности'
            })
        
        return consequences
    
    def calculate_whisper_effects(self, whisper_level):
        """
        Рассчитывает эффекты высокого уровня шёпота
        """
        display_whisper = min(whisper_level, self.MAX_DISPLAY_WHISPER)
        
        effects = []
        
        if whisper_level > self.MAX_DISPLAY_WHISPER:
            effects.append({
                'type': 'exceeded',
                'message': f'Шёпот превысил {self.MAX_DISPLAY_WHISPER}% (реальное: {whisper_level:.1f}%)',
                'effect': 'Непредсказуемые прозрения'
            })
        
        if display_whisper >= 100:
            effects.append({
                'type': 'enlightenment',
                'message': 'Полное понимание Бездны',
                'effect': '+50% к ментальной силе'
            })
        elif display_whisper >= 50:
            effects.append({
                'type': 'visions',
                'message': 'Частые видения',
                'effect': '+25% к интуиции'
            })
        elif display_whisper <= -50:
            effects.append({
                'type': 'resistance',
                'message': 'Сильное сопротивление Бездне',
                'effect': '+20% к защите'
            })
        
        return effects


# Тестирование
if __name__ == "__main__":
    calculator = GameCalculator()
    
    print("=== ТЕСТ GameCalculator с ограничениями отображения ===")
    
    # Тест 1: Нормальные значения
    print("\nТест 1: Нормальные значения")
    result = calculator.get_display_values(75, 60)
    print(f"Заражение: 75% → Отображение: {result['display_infection']}%")
    print(f"Шёпот: 60% → Отображение: {result['display_whisper']}%")
    print(f"Превышены: инфекция={result['has_exceeded_infection']}, шёпот={result['has_exceeded_whisper']}")
    
    # Тест 2: Превышенные значения
    print("\nТест 2: Превышенные значения")
    result = calculator.get_display_values(150, 250)
    print(f"Заражение: 150% → Отображение: {result['display_infection']}%")
    print(f"Шёпот: 250% → Отображение: {result['display_whisper']}%")
    print(f"Превышены: инфекция={result['has_exceeded_infection']}, шёпот={result['has_exceeded_whisper']}")
    print(f"Реальные значения: инфекция={result['real_infection']}%, шёпот={result['real_whisper']}%")
    
    # Тест 3: Риски и последствия
    print("\nТест 3: Оценка рисков")
    risk = calculator.calculate_infection_risk(85, 120)
    print(f"Риск при 85% заражения и 120% шёпота: {risk}")
    
    # Тест 4: Последствия высокого заражения
    print("\nТест 4: Последствия заражения")
    consequences = calculator.calculate_infection_consequences(95)
    for c in consequences:
        print(f"  {c['type']}: {c['message']} ({c['effect']})")
    
    # Тест 5: Эффекты шёпота
    print("\nТест 5: Эффекты шёпота")
    effects = calculator.calculate_whisper_effects(180)
    for e in effects:
        print(f"  {e['type']}: {e['message']} ({e['effect']})")
