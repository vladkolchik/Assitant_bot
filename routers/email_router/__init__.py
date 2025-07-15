from .router import email_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '✉️ Отправка email',
    'callback_data': 'email_mode',
    'order': 10  # После core модуля
} 