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

# ===== VISION API НАСТРОЙКИ (Изображения) =====
VISION_ENABLED = os.getenv("VISION_ENABLED", "true").lower() == "true"
VISION_QUALITY = os.getenv("VISION_QUALITY", "low").lower()  # Исправлено: было VISION_DETAIL
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "85"))  # Добавлено: качество сжатия JPEG
MAX_IMAGE_RESOLUTION = int(os.getenv("MAX_IMAGE_RESOLUTION", "1024"))
VISION_COST_WARNINGS = os.getenv("VISION_COST_WARNINGS", "true").lower() == "true"  # Исправлено: было SHOW_COST_WARNINGS

# ===== MEM0 ПАМЯТЬ НАСТРОЙКИ =====
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
MEM0_ENABLED = os.getenv("MEM0_ENABLED", "false").lower() == "true" and MEM0_API_KEY is not None

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

# Валидация VISION настроек
if VISION_QUALITY not in ["low", "high"]:
    print(f"⚠️  Неверное значение VISION_QUALITY: {VISION_QUALITY}")
    print("📋 Допустимые значения: 'low' или 'high'")
    VISION_QUALITY = "low"  # Fallback на экономичный режим

# Проверка поддержки Vision API моделью
# Базовые модели с Vision поддержкой
VISION_SUPPORTED_MODELS = ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
# Плюс все o4-модели (reasoning модели с Vision)
VISION_SUPPORTED_PREFIXES = ["o4-"]

# Проверяем поддержку Vision
vision_supported = (
    any(model in OPENAI_MODEL for model in VISION_SUPPORTED_MODELS) or
    any(OPENAI_MODEL.startswith(prefix) for prefix in VISION_SUPPORTED_PREFIXES)
)

if VISION_ENABLED and not vision_supported:
    print(f"⚠️  Модель {OPENAI_MODEL} не поддерживает изображения!")
    print(f"📋 Vision поддерживают: {', '.join(VISION_SUPPORTED_MODELS)} и o4-* модели")
    print("🔧 Отключаем поддержку изображений...")
    VISION_ENABLED = False

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
    
    # Vision API настройки
    'vision_enabled': VISION_ENABLED,
    'vision_quality': VISION_QUALITY,  # Исправлено: было vision_detail
    'max_image_size_mb': MAX_IMAGE_SIZE_MB,
    'image_quality': IMAGE_QUALITY,  # Добавлено: качество сжатия JPEG
    'max_image_resolution': MAX_IMAGE_RESOLUTION,
    'vision_cost_warnings': VISION_COST_WARNINGS,  # Исправлено: было show_cost_warnings
    
    # Mem0 память настройки
    'mem0_enabled': MEM0_ENABLED,
    'mem0_api_key': MEM0_API_KEY,
}

# Создаем папку для временных аудио файлов
TEMP_AUDIO_PATH = module_dir / AUDIO_TEMP_DIR
TEMP_AUDIO_PATH.mkdir(exist_ok=True)

# Конвертируем относительные пути в абсолютные для использования в модуле
MODULE_CONFIG['temp_audio_path'] = TEMP_AUDIO_PATH 