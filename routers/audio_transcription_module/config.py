"""
Конфигурация модуля транскрипции аудио через OpenAI Whisper
"""
import os
from pathlib import Path

# Путь к модулю
MODULE_DIR = Path(__file__).parent

def load_env_file(file_path: Path) -> dict:
    """Загружает переменные из .env файла"""
    env_vars = {}
    if file_path.exists():
        print(f"✅ Загружен .env из {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    else:
        print(f"⚠️  Файл .env не найден в {file_path.parent}")
        print("📋 Скопируйте .env.example в .env и заполните значения")
    return env_vars

# Загружаем переменные из .env файла модуля
module_env = load_env_file(MODULE_DIR / '.env')

# Обязательные переменные
REQUIRED_VARS = ['OPENAI_API_KEY']
missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]

if missing_vars:
    print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
    OPENAI_API_KEY = None
else:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Конфигурация модуля
MODULE_CONFIG = {
    'model': os.getenv('WHISPER_MODEL', 'whisper-1'),
    'language': os.getenv('WHISPER_LANGUAGE', 'auto'),  # 'auto' для автоопределения
    'temperature': float(os.getenv('WHISPER_TEMPERATURE', '0')),
    'max_file_size': 25 * 1024 * 1024,  # 25MB - лимит Telegram для аудио
    'supported_formats': ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']
} 