"""
Конфигурация ChatGPT модуля
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла модуля
module_dir = Path(__file__).parent
env_path = module_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠️  Файл .env не найден в {module_dir}")
    print(f"📋 Скопируйте .env.example в .env и заполните значения")

# Переменные модуля
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Валидация обязательных переменных
REQUIRED_VARS = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    print(f"❌ Отсутствуют переменные в .env: {', '.join(missing_vars)}")
    print(f"📋 Скопируйте .env.example в .env и заполните значения")

# Конфигурация модуля
MODULE_CONFIG = {
    'api_key': OPENAI_API_KEY,
    'model': OPENAI_MODEL,
    'max_tokens': OPENAI_MAX_TOKENS,
    'temperature': OPENAI_TEMPERATURE,
    'timeout': 30,  # секунды для запросов
} 