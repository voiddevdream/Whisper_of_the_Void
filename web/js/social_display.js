
/**
 * JavaScript для отображения социальных профилей
 */

class SocialProfileDisplay {
    constructor() {
        this.profiles = {};
    }
    
    /**
     * Загружает профиль игрока
     */
    async loadProfile(playerId) {
        try {
            const response = await fetch(`/data/players/social_profile_${playerId}.json`);
            if (!response.ok) {
                throw new Error('Профиль не найден');
            }
            
            const profile = await response.json();
            this.profiles[playerId] = profile;
            return profile;
            
        } catch (error) {
            console.warn(`Не удалось загрузить профиль игрока ${playerId}:`, error);
            return this.getDefaultProfile(playerId);
        }
    }
    
    /**
     * Возвращает профиль по умолчанию
     */
    getDefaultProfile(playerId) {
        return {
            player_id: playerId,
            total_score: 0,
            icons: {
                main: { icon: "🌔", name: "Полумесяц" },
                sub: { icon: "•", name: "Неизвестно" },
                display: "🌔•",
                full_name: "Полумесяц • Неизвестно"
            },
            description: "Новый в Хёльвании. Его социальный профиль ещё формируется.",
            category_distribution: {
                percentages: {
                    betrayal: 0,
                    hostility: 0,
                    contract: 0,
                    alliance: 0,
                    passion: 0
                }
            },
            trend: "stable"
        };
    }
    
    /**
     * Отображает профиль в HTML-контейнере
     */
    renderProfile(containerId, playerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Контейнер ${containerId} не найден`);
            return;
        }
        
        this.loadProfile(playerId).then(profile => {
            container.innerHTML = this.generateProfileHTML(profile);
            this.animateProfile(containerId);
        });
    }
    
    /**
     * Генерирует HTML для профиля
     */
    generateProfileHTML(profile) {
        const scoreClass = this.getScoreClass(profile.total_score);
        
        return `
            <div class="social-profile" data-player="${profile.player_id}">
                <div class="profile-header">
                    <div class="main-icons">
                        <span class="main-icon">${profile.icons.main.icon}</span>
                        <span class="sub-icon">${profile.icons.sub.icon}</span>
                    </div>
                    
                    <h3 class="profile-name">${profile.icons.full_name}</h3>
                    <p class="profile-subtitle">Социальный профиль</p>
                    
                    <div class="score-display">
                        <div class="score-number ${scoreClass}">
                            ${profile.total_score > 0 ? '+' : ''}${profile.total_score}
                        </div>
                        <div class="score-meter">
                            <div class="score-fill ${scoreClass}" 
                                 style="width: ${Math.abs(profile.total_score)}%">
                            </div>
                        </div>
                        <div class="score-label">/100</div>
                    </div>
                </div>
                
                <div class="category-distribution">
                    <h4>Распределение по категориям:</h4>
                    ${this.generateCategoryBarsHTML(profile.category_distribution.percentages)}
                </div>
                
                <div class="profile-description">
                    ${profile.description}
                </div>
                
                <div class="profile-trend trend-${profile.trend}">
                    Тренд: ${this.getTrendText(profile.trend)}
                </div>
            </div>
        `;
    }
    
    /**
     * Генерирует HTML для полосок категорий
     */
    generateCategoryBarsHTML(percentages) {
        const categories = [
            { id: 'betrayal', name: 'Измена', icon: '🗡️' },
            { id: 'hostility', name: 'Вражда', icon: '⚔️' },
            { id: 'contract', name: 'Договор', icon: '🤝' },
            { id: 'alliance', name: 'Союз', icon: '🕊️' },
            { id: 'passion', name: 'Страсть', icon: '🔥' }
        ];
        
        return categories.map(cat => `
            <div class="category-item">
                <span class="category-icon">${cat.icon}</span>
                <span class="category-name">${cat.name}</span>
                <div class="category-bar-container">
                    <div class="category-bar ${cat.id}" 
                         style="width: ${percentages[cat.id] || 0}%">
                    </div>
                </div>
                <span class="category-percentage">${percentages[cat.id] || 0}%</span>
            </div>
        `).join('');
    }
    
    /**
     * Определяет класс для балла
     */
    getScoreClass(score) {
        if (score < -10) return 'negative';
        if (score > 10) return 'positive';
        return 'neutral';
    }
    
    /**
     * Возвращает текст тренда
     */
    getTrendText(trend) {
        const trends = {
            'improving': 'Улучшение',
            'worsening': 'Ухудшение',
            'stable': 'Стабильно'
        };
        return trends[trend] || 'Неизвестно';
    }
    
    /**
     * Анимирует появление профиля
     */
    animateProfile(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            container.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
        
        // Анимация полосок
        setTimeout(() => {
            const bars = container.querySelectorAll('.category-bar, .score-fill');
            bars.forEach(bar => {
                const currentWidth = bar.style.width;
                bar.style.width = '0';
                
                setTimeout(() => {
                    bar.style.transition = 'width 1s ease';
                    bar.style.width = currentWidth;
                }, 300);
            });
        }, 600);
    }
    
    /**
     * Создаёт компактный бейдж для игрока
     */
    createPlayerBadge(playerId, container) {
        this.loadProfile(playerId).then(profile => {
            const badge = document.createElement('div');
            badge.className = 'player-social-badge';
            badge.innerHTML = `
                <span class="badge-icons">${profile.icons.display}</span>
                <span class="badge-score">${profile.total_score > 0 ? '+' : ''}${profile.total_score}</span>
            `;
            
            // Подсказка при наведении
            badge.title = `${profile.icons.full_name}\n${profile.description}`;
            
            container.appendChild(badge);
        });
    }
}

// Экспортируем класс для использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SocialProfileDisplay;
}
