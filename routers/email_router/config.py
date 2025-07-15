"""
Конфигурация email модуля
"""
from config import FROM_EMAIL, DEFAULT_RECIPIENT

# Локальные настройки email модуля
EMAIL_CONFIG = {
    'from_email': FROM_EMAIL,
    'default_recipient': DEFAULT_RECIPIENT,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 465,
    'use_ssl': True,
}

# Экспорт для удобного использования в модуле
GMAIL_ADDRESS = FROM_EMAIL
DEFAULT_EMAIL_RECIPIENT = DEFAULT_RECIPIENT 