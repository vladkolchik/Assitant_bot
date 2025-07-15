from .router import core_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🏠 Главное меню', 
    'callback_data': 'main_menu',
    'order': 1  # Самый первый в меню
} 