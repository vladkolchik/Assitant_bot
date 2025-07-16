"""
Сервисы для работы с аудио в ChatGPT модуле
Поддержка Whisper API и локального Whisper
"""
import asyncio
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import aiohttp

from aiogram import Bot
from aiogram.types import Audio, Voice, VideoNote

from .config import MODULE_CONFIG

logger = logging.getLogger(__name__)

# Проверяем доступность библиотек
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(MODULE_CONFIG['api_key'])
    if MODULE_CONFIG['api_key']:
        openai_client = OpenAI(api_key=MODULE_CONFIG['api_key'])
    else:
        openai_client = None
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None
    logger.warning("OpenAI library not available")

try:
    import whisper
    WHISPER_LOCAL_AVAILABLE = True
except ImportError:
    WHISPER_LOCAL_AVAILABLE = False
    logger.warning("Local Whisper not available. Install with: pip install openai-whisper")

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    logger.warning("FFmpeg not available. Install with: pip install ffmpeg-python")


class AudioService:
    """Сервис для работы с аудио файлами"""
    
    def __init__(self):
        self.temp_dir = MODULE_CONFIG['temp_audio_path']
        self.max_size_mb = MODULE_CONFIG['max_audio_size_mb']
        self.max_duration_sec = MODULE_CONFIG['max_audio_duration_sec']
        self.whisper_mode = MODULE_CONFIG['whisper_mode']
        self.auto_cleanup = MODULE_CONFIG['auto_cleanup_temp_files']
        
        # Локальная модель Whisper (загружается при первом использовании)
        self._local_whisper_model = None
    
    async def validate_audio_file(self, file_size: Optional[int], duration: Optional[int]) -> Tuple[bool, str]:
        """Валидация размера и длительности аудио файла"""
        if file_size and file_size > self.max_size_mb * 1024 * 1024:
            return False, f"Файл слишком большой. Максимум: {self.max_size_mb} МБ"
        
        if duration and duration > self.max_duration_sec:
            max_minutes = self.max_duration_sec // 60
            return False, f"Аудио слишком длинное. Максимум: {max_minutes} минут"
        
        return True, "OK"
    
    async def download_audio_file(self, bot: Bot, file_id: str, file_extension: str = "ogg") -> Optional[Path]:
        """Скачивание аудио файла с Telegram серверов"""
        try:
            # Получаем информацию о файле
            file_info = await bot.get_file(file_id)
            if not file_info.file_path:
                logger.error(f"Не удалось получить путь к файлу {file_id}")
                return None
            
            # Создаем временный файл
            temp_filename = f"audio_{file_id[:10]}.{file_extension}"
            temp_file_path = self.temp_dir / temp_filename
            
            # Скачиваем файл
            async with aiohttp.ClientSession() as session:
                download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
                async with session.get(download_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(temp_file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"Аудио скачано: {temp_file_path}")
                        return temp_file_path
                    else:
                        logger.error(f"Ошибка скачивания: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка при скачивании аудио: {e}")
            return None
    
    async def convert_audio_to_wav(self, input_path: Path) -> Optional[Path]:
        """Конвертация аудио в WAV формат для локального Whisper"""
        if not FFMPEG_AVAILABLE:
            logger.warning("FFmpeg недоступен для конвертации")
            return input_path  # Возвращаем оригинальный файл
        
        try:
            output_path = input_path.with_suffix('.wav')
            
            # Конвертируем с помощью ffmpeg
            await asyncio.to_thread(
                ffmpeg.input(str(input_path))
                .output(str(output_path), acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run,
                quiet=True
            )
            
            logger.info(f"Аудио сконвертировано: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка конвертации аудио: {e}")
            return input_path  # Возвращаем оригинальный файл
    
    async def transcribe_with_api(self, audio_path: Path) -> Optional[str]:
        """Транскрипция через OpenAI Whisper API"""
        if not OPENAI_AVAILABLE or not openai_client:
            return None
        
        try:
            # Подготавливаем параметры для API
            api_params = {
                'model': MODULE_CONFIG['whisper_model'],
                'file': None,  # Будет установлен ниже
            }
            
            # Добавляем язык только если он не 'auto' (API не поддерживает 'auto')
            if MODULE_CONFIG['whisper_language'] and MODULE_CONFIG['whisper_language'].lower() != 'auto':
                api_params['language'] = MODULE_CONFIG['whisper_language']
            
            with open(audio_path, 'rb') as audio_file:
                api_params['file'] = audio_file
                response = await asyncio.to_thread(
                    openai_client.audio.transcriptions.create,
                    **api_params
                )
                
            transcription = response.text.strip()
            logger.info(f"Транскрипция через API успешна: {len(transcription)} символов")
            return transcription
            
        except Exception as e:
            logger.error(f"Ошибка транскрипции через API: {e}")
            return None
    
    async def transcribe_with_local_whisper(self, audio_path: Path) -> Optional[str]:
        """Транскрипция через локальный Whisper"""
        if not WHISPER_LOCAL_AVAILABLE:
            return None
        
        try:
            # Загружаем модель (только при первом использовании)
            if self._local_whisper_model is None:
                model_name = MODULE_CONFIG['local_whisper_model']
                logger.info(f"Загрузка локальной модели Whisper: {model_name}")
                self._local_whisper_model = await asyncio.to_thread(
                    whisper.load_model, model_name
                )
            
            # Транскрибируем
            result = await asyncio.to_thread(
                self._local_whisper_model.transcribe,
                str(audio_path),
                language=MODULE_CONFIG['whisper_language']
            )
            
            transcription = result["text"].strip()
            logger.info(f"Локальная транскрипция успешна: {len(transcription)} символов")
            return transcription
            
        except Exception as e:
            logger.error(f"Ошибка локальной транскрипции: {e}")
            return None
    
    async def transcribe_audio(self, audio_path: Path) -> Tuple[Optional[str], str]:
        """
        Основная функция транскрипции
        Возвращает: (транскрипция, метод_использования)
        """
        if self.whisper_mode == "api":
            transcription = await self.transcribe_with_api(audio_path)
            if transcription:
                return transcription, "OpenAI Whisper API"
            
            # Fallback на локальный Whisper если API не сработал
            logger.info("API не сработал, пробуем локальный Whisper...")
            
        # Используем локальный Whisper
        wav_path = await self.convert_audio_to_wav(audio_path)
        if wav_path is None:
            return None, "Ошибка конвертации аудио"
        
        transcription = await self.transcribe_with_local_whisper(wav_path)
        
        if transcription:
            return transcription, "Локальный Whisper"
        
        return None, "Ошибка транскрипции"
    
    async def cleanup_temp_files(self, *file_paths: Path):
        """Очистка временных файлов"""
        if not self.auto_cleanup:
            return
        
        for file_path in file_paths:
            try:
                if file_path and file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Удален временный файл: {file_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить файл {file_path}: {e}")
    
    async def process_telegram_audio(self, bot: Bot, audio_file) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Полная обработка аудио из Telegram
        
        Args:
            bot: Экземпляр Telegram бота
            audio_file: Voice, Audio или VideoNote объект
        
        Returns:
            Tuple[transcription, method_used, error_message]
        """
        temp_files = []
        
        try:
            # Определяем тип аудио и валидируем
            if isinstance(audio_file, Voice):
                file_id = audio_file.file_id
                file_size = audio_file.file_size
                duration = audio_file.duration
                extension = "ogg"
            elif isinstance(audio_file, VideoNote):
                file_id = audio_file.file_id
                file_size = audio_file.file_size
                duration = audio_file.duration
                extension = "mp4"
            elif isinstance(audio_file, Audio):
                file_id = audio_file.file_id
                file_size = audio_file.file_size
                duration = audio_file.duration
                extension = "mp3"
            else:
                return None, "Ошибка", "Неподдерживаемый тип аудио файла"
            
            # Валидация размера и длительности
            is_valid, validation_message = await self.validate_audio_file(file_size, duration)
            if not is_valid:
                return None, "Ошибка", validation_message
            
            # Скачиваем файл
            audio_path = await self.download_audio_file(bot, file_id, extension)
            if not audio_path:
                return None, "Ошибка", "Не удалось скачать аудио файл"
            
            temp_files.append(audio_path)
            
            # Транскрибируем
            transcription, method = await self.transcribe_audio(audio_path)
            
            if not transcription:
                return None, "Ошибка", "Не удалось распознать речь в аудио"
            
            return transcription, method, None
            
        except Exception as e:
            logger.error(f"Ошибка обработки аудио: {e}")
            return None, "Ошибка", f"Произошла ошибка: {str(e)}"
            
        finally:
            # Очищаем временные файлы
            await self.cleanup_temp_files(*temp_files)


# Глобальный экземпляр сервиса
audio_service = AudioService()


# Вспомогательные функции для упрощения использования
async def transcribe_voice_message(bot: Bot, voice: Voice) -> Tuple[Optional[str], str, Optional[str]]:
    """Транскрипция голосового сообщения"""
    return await audio_service.process_telegram_audio(bot, voice)

async def transcribe_video_note(bot: Bot, video_note: VideoNote) -> Tuple[Optional[str], str, Optional[str]]:
    """Транскрипция кружочка"""
    return await audio_service.process_telegram_audio(bot, video_note)

async def transcribe_audio_file(bot: Bot, audio: Audio) -> Tuple[Optional[str], str, Optional[str]]:
    """Транскрипция аудио файла"""
    return await audio_service.process_telegram_audio(bot, audio) 