from .router import test_module_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🧪 Тест модуль',
    'callback_data': 'test_mode',
    'order': 15  # Между email (10) и id_module (20)
} 