"""
Модуль игровых расчетов для Whisper of the Void
Содержит формулы для прогрессии, заражения, шёпота и т.д.
"""

class GameCalculator:
    """Калькулятор игровых формул"""
    
    def __init__(self):
        # Константы баланса (можно вынести в config.json)
        self.BASE_CREDITS = 5
        self.BASE_INFECTION = 0.2
        self.CREDITS_PER_POST = 10
        self.WHISPER_PER_TOPIC = 3
        self.INFECTION_REDUCTION_PER_POST = 0.03
        
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
        
        # 4. Можете добавить сложные формулы:
        # - Влияние расы (если добавите в данные)
        # - Шкалу безумия при высоком шёпоте
        # - Шанс превращения при 100% заражении
        
        return {
            'credits': player_data['data'].get('credits', 0) + credits_change,
            'infection': player_data['data'].get('infection', 0) + infection_change,
            'whisper': player_data['data'].get('whisper', 0) + whisper_change,
            'changes': {
                'credits_change': credits_change,
                'infection_change': infection_change,
                'whisper_change': whisper_change,
                'posts_used': post_count,
                'topics_used': unique_topics
            }
        }
    
    def calculate_infection_risk(self, current_infection, whisper_level):
        """Рассчитывает риск событий на основе заражения и шёпота"""
        if current_infection >= 100:
            return "Требуется превращение"
        elif current_infection >= 80:
            return "Высокий риск"
        elif whisper_level >= 150:
            return "Влияние Бездны"
        return "Стабильно"
    
    # Добавьте другие методы по мере развития:
    # - calculate_mastery_gain()
    # - calculate_race_transformation()
    # - calculate_quest_rewards()
