"""
Тестирование игровых формул для Whisper of the Void
Запуск: python tests/test_formulas.py
"""

import sys
import os

# Добавляем папку scripts в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from game_calculator import GameCalculator

def test_basic_calculations():
    """Тест базовых расчетов"""
    print("🧪 Тестируем базовые формулы...")
    
    calc = GameCalculator()
    
    # Тестовые данные
    test_player = {
        'data': {'credits': 100, 'infection': 50, 'whisper': 30}
    }
    
    # Тест 1: Без активности
    result = calc.calculate_player_progression(
        test_player, 
        {'post_count': 0, 'unique_topics': 0}
    )
    
    print(f"   Без активности: +{result['changes']['credits_change']}💰")
    assert result['changes']['credits_change'] == 5  # BASE_CREDITS
    
    # Тест 2: С активностью
    result = calc.calculate_player_progression(
        test_player,
        {'post_count': 3, 'unique_topics': 2}
    )
    
    print(f"   3 поста, 2 темы: +{result['changes']['credits_change']}💰")
    assert result['changes']['credits_change'] == 5 + (3 * 10)  # BASE + посты
    
    # Тест 3: Риск заражения
    risk = calc.calculate_infection_risk(85, 100)
    print(f"   Риск при 85% заражения: {risk}")
    
    print("✅ Базовые тесты пройдены!\n")

def test_edge_cases():
    """Тест крайних случаев"""
    print("🧪 Тестируем крайние случаи...")
    
    calc = GameCalculator()
    
    # Игрок с максимальными значениями
    max_player = {
        'data': {'credits': 9999, 'infection': 99, 'whisper': 290}
    }
    
    result = calc.calculate_player_progression(
        max_player,
        {'post_count': 10, 'unique_topics': 5}
    )
    
    print(f"   Активный топ-игрок:")
    print(f"     Кредиты: {result['credits']} (+{result['changes']['credits_change']})")
    print(f"     Заражение: {result['infection']:.1f}% (+{result['changes']['infection_change']:.2f})")
    print(f"     Шёпот: {result['whisper']}% (+{result['changes']['whisper_change']})")
    
    # Проверяем, что шёпот не превысил 300%
    assert result['whisper'] <= 300
    
    print("✅ Крайние случаи обработаны!\n")

def compare_with_old_logic():
    """Сравнение новой логики со старой (из core_parser)"""
    print("🧪 Сравниваем со старой логикой...")
    
    calc = GameCalculator()
    
    # Данные Void
    void_data = {
        'username': 'Void',
        'data': {'credits': 200, 'infection': 13, 'whisper': 312},
        'forum_stats': {'last_visit': 'Сегодня'}
    }
    
    # Старая логика (из текущего core_parser.py)
    def old_calculation(activity):
        credits = 5
        infection = 0.2
        whisper = 0
        
        if activity.get('post_count', 0) > 0:
            credits += activity['post_count'] * 10
            whisper += activity.get('unique_topics', 0) * 3
            infection -= min(0.15, activity['post_count'] * 0.03)
        
        return credits, infection, whisper
    
    # Сравниваем
    activity = {'post_count': 2, 'unique_topics': 1}
    
    old = old_calculation(activity)
    new = calc.calculate_player_progression(void_data, activity)
    
    print("   Старая логика: " + 
          f"+{old[0]}💰, {old[1]:+.2f}%🦠, {old[2]:+.1f}%👁️")
    print("   Новая логика:  " +
          f"+{new['changes']['credits_change']}💰, " +
          f"{new['changes']['infection_change']:+.2f}%🦠, " +
          f"{new['changes']['whisper_change']:+.1f}%👁️")
    
    print("✅ Сравнение завершено!\n")

if __name__ == "__main__":
    print("=" * 50)
    print("🎮 ТЕСТИРОВАНИЕ ФОРМУЛ WHISPER OF THE VOID")
    print("=" * 50)
    
    test_basic_calculations()
    test_edge_cases()
    compare_with_old_logic()
    
    print("🎉 Все тесты успешно пройдены!")
    print("Следующий шаг: интегрируйте GameCalculator в core_parser.py")
