"""
Конфигурация ChatGPT + Whisper модуля
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
    print(f"📋 Скопируйте env.example в .env и заполните значения")

# ===== CHATGPT НАСТРОЙКИ =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
OPENAI_MAX_COMPLETION_TOKENS = int(os.getenv("OPENAI_MAX_COMPLETION_TOKENS", "5000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Автоматически выбираем правильное значение токенов в зависимости от модели
if any(OPENAI_MODEL.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']):
    # Для reasoning-моделей используем max_completion_tokens (или увеличенное значение)
    EFFECTIVE_MAX_TOKENS = OPENAI_MAX_COMPLETION_TOKENS if OPENAI_MAX_COMPLETION_TOKENS > OPENAI_MAX_TOKENS else max(OPENAI_MAX_TOKENS, 5000)
else:
    # Для остальных моделей используем max_tokens
    EFFECTIVE_MAX_TOKENS = OPENAI_MAX_TOKENS

# ===== WHISPER НАСТРОЙКИ =====
WHISPER_MODE = os.getenv("WHISPER_MODE", "api").lower()  # "api" или "local"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")  # Для API
LOCAL_WHISPER_MODEL = os.getenv("LOCAL_WHISPER_MODEL", "base")  # Для локального
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru")  # Язык распознавания

# ===== АУДИО НАСТРОЙКИ =====
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
MAX_AUDIO_DURATION_SEC = int(os.getenv("MAX_AUDIO_DURATION_SEC", "300"))
AUDIO_TEMP_DIR = os.getenv("AUDIO_TEMP_DIR", "temp_audio")
AUTO_CLEANUP_TEMP_FILES = os.getenv("AUTO_CLEANUP_TEMP_FILES", "true").lower() == "true"

# Валидация обязательных переменных
REQUIRED_VARS = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    print(f"❌ Отсутствуют переменные в .env: {', '.join(missing_vars)}")
    print(f"📋 Скопируйте env.example в .env и заполните значения")

# Валидация WHISPER_MODE
if WHISPER_MODE not in ["api", "local"]:
    print(f"⚠️  Неверное значение WHISPER_MODE: {WHISPER_MODE}")
    print("📋 Допустимые значения: 'api' или 'local'")
    WHISPER_MODE = "api"  # Fallback на API

# Валидация модели и токенов
if any(OPENAI_MODEL.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']) and EFFECTIVE_MAX_TOKENS < 1000:
    print(f"⚠️  Для reasoning-модели {OPENAI_MODEL} рекомендуется max_tokens >= 5000")
    print(f"📋 Текущее значение: {EFFECTIVE_MAX_TOKENS}")

# Конфигурация модуля
MODULE_CONFIG = {
    # ChatGPT настройки
    'api_key': OPENAI_API_KEY,
    'model': OPENAI_MODEL,
    'max_tokens': EFFECTIVE_MAX_TOKENS,  # Используем правильное значение для модели
    'original_max_tokens': OPENAI_MAX_TOKENS,  # Оригинальное значение для отображения
    'max_completion_tokens': OPENAI_MAX_COMPLETION_TOKENS,  # Для o1-моделей
    'temperature': OPENAI_TEMPERATURE,
    'timeout': 30,  # секунды для запросов
    
    # Whisper настройки
    'whisper_mode': WHISPER_MODE,
    'whisper_model': WHISPER_MODEL,
    'local_whisper_model': LOCAL_WHISPER_MODEL,
    'whisper_language': WHISPER_LANGUAGE,
    
    # Аудио настройки
    'max_audio_size_mb': MAX_AUDIO_SIZE_MB,
    'max_audio_duration_sec': MAX_AUDIO_DURATION_SEC,
    'audio_temp_dir': AUDIO_TEMP_DIR,
    'auto_cleanup_temp_files': AUTO_CLEANUP_TEMP_FILES,
}

# Создаем папку для временных аудио файлов
TEMP_AUDIO_PATH = module_dir / AUDIO_TEMP_DIR
TEMP_AUDIO_PATH.mkdir(exist_ok=True)

# Конвертируем относительные пути в абсолютные для использования в модуле
MODULE_CONFIG['temp_audio_path'] = TEMP_AUDIO_PATH 