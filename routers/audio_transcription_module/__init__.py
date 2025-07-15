from .router import audio_router

# Конфигурация для главного меню
MENU_CONFIG = {
    'text': '🎤 Транскрипция',
    'callback_data': 'audio_transcription',
    'order': 12  # После ChatGPT (15), перед другими модулями
} 