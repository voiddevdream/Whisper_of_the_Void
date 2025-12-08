# test_formulas.py
from game_calculator import GameCalculator

def test_formulas():
    print("🧪 Тестирование формул Whisper of the Void")
    print("=" * 50)
    
    calculator = GameCalculator()
    
    # Тестовые сценарии
    test_cases = [
        {
            'name': 'Активный игрок',
            'player': {'credits': 100, 'infection': 20, 'whisper': 30, 'status_raw': 'К:+50 З:+5% Ш:+10%', 'last_visit': 'Сегодня'},
            'activity': {'post_count': 5, 'unique_topics': 3},
            'days': 30
        },
        {
            'name': 'Неактивный игрок',
            'player': {'credits': 50, 'infection': 60, 'whisper': 80, 'status_raw': 'К:+0 З:+0% Ш:+0%', 'last_visit': '2025-11-01'},
            'activity': {'post_count': 0, 'unique_topics': 0},
            'days': 60
        },
        {
            'name': 'Новичок с бонусами',
            'player': {'credits': 0, 'infection': 5, 'whisper': 0, 'status_raw': 'К:+200 З:+13% Ш:+312%', 'last_visit': 'Сегодня'},
            'activity': {'post_count': 2, 'unique_topics': 1},
            'days': 7
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}:")
        print(f"   Исходные: {test['player']['credits']}💰, {test['player']['infection']}%🦠, {test['player']['whisper']}%👁️")
        
        result = calculator.calculate_player_progression(
            test['player'],
            test['activity'],
            test['days']
        )
        
        print(f"   Новые: {result['credits']}💰, {result['infection']}%🦠, {result['whisper']}%👁️")
        print(f"   Изменения: {result['changes']}")

if __name__ == "__main__":
    test_formulas()
