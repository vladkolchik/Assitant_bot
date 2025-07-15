from .router import api_example_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🌐 API Пример',
    'callback_data': 'api_example_mode',
    'order': 25  # После основных модулей
} 