from .router import voice_assistant_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🎤 Голосовой ассистент',
    'callback_data': 'voice_assistant',
    'order': 10  # Высокий приоритет - первая позиция среди модулей
} 