"""
Конфигурация модуля голосового ассистента
Объединяет транскрипцию Whisper и ChatGPT
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла модуля
module_dir = Path(__file__).parent
env_path = module_dir / '.env'
load_dotenv(env_path)

# OpenAI API ключ (общий для Whisper и ChatGPT)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Конфигурация модуля
MODULE_CONFIG = {
    # Whisper параметры
    'whisper_model': 'whisper-1',
    'whisper_language': 'auto',  # 'auto' для автоопределения или код языка (ru, en и т.д.)
    'whisper_temperature': 0.2,
    
    # ChatGPT параметры
    'chatgpt_model': 'gpt-3.5-turbo',
    'chatgpt_max_tokens': 1000,
    'chatgpt_temperature': 0.7,
    
    # Ограничения файлов
    'max_file_size': 25 * 1024 * 1024,  # 25 МБ (лимит Whisper API)
    'supported_formats': ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg'],
    
    # Система промпт для ChatGPT
    'system_prompt': "Вы полезный AI ассистент. Пользователь отправил голосовое сообщение, которое было транскрибировано. Отвечайте на русском языке, будьте дружелюбны и информативны. Если в транскрипции есть ошибки, попытайтесь понять истинный смысл.",
    
    # Таймауты
    'whisper_timeout': 60,  # секунды
    'chatgpt_timeout': 30,  # секунды
}

# Информация для отображения в меню
MODULE_INFO = {
    'name': 'Голосовой ассистент',
    'description': 'Распознавание речи + ChatGPT',
    'version': '1.0.0'
} 