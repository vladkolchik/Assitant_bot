"""
Конфигурация email модуля - модульное управление секретами
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла модуля
module_dir = Path(__file__).parent
env_path = module_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Email модуль: загружен .env из {module_dir}")
else:
    print(f"⚠️  Email модуль: файл .env не найден в {module_dir}")
    print(f"📋 Скопируйте .env.example в .env и заполните значения")

# Переменные модуля
FROM_EMAIL = os.getenv("FROM_EMAIL")
DEFAULT_RECIPIENT = os.getenv("DEFAULT_RECIPIENT")

# Валидация обязательных переменных
REQUIRED_VARS = {
    "FROM_EMAIL": FROM_EMAIL,
    "DEFAULT_RECIPIENT": DEFAULT_RECIPIENT,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    print(f"❌ Email модуль: отсутствуют обязательные переменные: {', '.join(missing_vars)}")

# Локальные настройки email модуля
EMAIL_CONFIG = {
    'from_email': FROM_EMAIL,
    'default_recipient': DEFAULT_RECIPIENT,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 465,
    'use_ssl': True,
    'is_configured': bool(FROM_EMAIL and DEFAULT_RECIPIENT),
}

# Экспорт для удобного использования в модуле
GMAIL_ADDRESS = FROM_EMAIL
DEFAULT_EMAIL_RECIPIENT = DEFAULT_RECIPIENT 
IS_CONFIGURED = EMAIL_CONFIG['is_configured'] 