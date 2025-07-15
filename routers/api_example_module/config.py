"""
Конфигурация api_example_module - демонстрация модульного управления секретами
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла модуля
module_dir = Path(__file__).parent
env_path = module_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружен .env из {module_dir}")
else:
    print(f"⚠️  Файл .env не найден в {module_dir}")
    print(f"📋 Скопируйте env.example в .env и заполните значения")

# Переменные модуля
MY_API_KEY = os.getenv("MY_API_KEY")
MY_SERVICE_URL = os.getenv("MY_SERVICE_URL", "https://api.example.com")
MY_WEBHOOK_SECRET = os.getenv("MY_WEBHOOK_SECRET")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Валидация обязательных переменных
REQUIRED_VARS = {
    "MY_API_KEY": MY_API_KEY,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")

# Конфигурация модуля
MODULE_CONFIG = {
    'api_key': MY_API_KEY,
    'service_url': MY_SERVICE_URL,
    'webhook_secret': MY_WEBHOOK_SECRET,
    'timeout': API_TIMEOUT,
    'is_configured': bool(MY_API_KEY),
}

# Экспорт для удобного использования
API_KEY = MY_API_KEY
SERVICE_URL = MY_SERVICE_URL
IS_CONFIGURED = MODULE_CONFIG['is_configured'] 