from .router import chatgpt_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🤖 ChatGPT',
    'callback_data': 'chatgpt_mode',
    'order': 15  # Между email (10) и test (20)
} 