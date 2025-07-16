"""
Модуль голосового ассистента
Объединяет транскрипцию Whisper и обработку ChatGPT
"""
import asyncio
import os
import tempfile
import time
from pathlib import Path
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, Audio, Voice, VideoNote, Document
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .config import MODULE_CONFIG, OPENAI_API_KEY
from .messages import MESSAGES

# Состояния модуля
class VoiceAssistantStates(StatesGroup):
    waiting_for_audio = State()

voice_assistant_router = Router()

# Проверяем наличие OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(OPENAI_API_KEY)
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None
    print("⚠️ OpenAI library not installed. Run: pip install openai")

def get_back_menu():
    """Клавиатура для возврата в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def format_file_size(size_bytes: int) -> float:
    """Форматирует размер файла в МБ"""
    return round(size_bytes / (1024 * 1024), 2)

def get_file_extension(filename: str) -> str:
    """Получает расширение файла"""
    return Path(filename).suffix.lower() if filename else ''

@voice_assistant_router.callback_query(F.data == "voice_assistant")
async def activate_voice_assistant(callback: CallbackQuery, state: FSMContext):
    """Активация режима голосового ассистента"""
    if not callback.message:
        return
        
    if not OPENAI_AVAILABLE:
        await callback.message.edit_text(  # type: ignore
            MESSAGES["not_configured"], 
            reply_markup=get_back_menu()
        )
        return
    
    await state.set_state(VoiceAssistantStates.waiting_for_audio)
    await callback.message.edit_text(  # type: ignore
        MESSAGES["welcome"],
        reply_markup=get_back_menu()
    )
    await callback.answer("🎤 Голосовой ассистент активирован!")

@voice_assistant_router.message(StateFilter(VoiceAssistantStates.waiting_for_audio), F.voice)
async def handle_voice_message(message: Message, state: FSMContext):
    """Обработка голосовых сообщений"""
    if not OPENAI_AVAILABLE or not openai_client or not message.voice:
        return
    
    await process_audio_with_chatgpt(message, message.voice.file_id, "voice.ogg", message.voice.file_size or 0)

@voice_assistant_router.message(StateFilter(VoiceAssistantStates.waiting_for_audio), F.audio)
async def handle_audio_file(message: Message, state: FSMContext):
    """Обработка аудиофайлов"""
    if not OPENAI_AVAILABLE or not openai_client or not message.audio:
        return
    
    # Проверяем размер файла
    if message.audio.file_size and message.audio.file_size > MODULE_CONFIG['max_file_size']:
        size_mb = format_file_size(message.audio.file_size)
        await message.reply(
            MESSAGES["file_too_large"].format(size=size_mb),
            reply_markup=get_back_menu()
        )
        return
    
    # Проверяем формат файла
    filename = message.audio.file_name or "audio.mp3"
    file_ext = get_file_extension(filename)
    if file_ext not in MODULE_CONFIG['supported_formats']:
        await message.reply(
            MESSAGES["unsupported_format"].format(format=file_ext),
            reply_markup=get_back_menu()
        )
        return
    
    await process_audio_with_chatgpt(message, message.audio.file_id, filename, message.audio.file_size or 0)

@voice_assistant_router.message(StateFilter(VoiceAssistantStates.waiting_for_audio), F.video_note)
async def handle_video_note(message: Message, state: FSMContext):
    """Обработка кружочков (видеосообщений)"""
    if not OPENAI_AVAILABLE or not openai_client or not message.video_note:
        return
    
    await process_audio_with_chatgpt(message, message.video_note.file_id, "video_note.mp4", message.video_note.file_size or 0)

@voice_assistant_router.message(StateFilter(VoiceAssistantStates.waiting_for_audio), F.document)
async def handle_document_audio(message: Message, state: FSMContext):
    """Обработка аудиофайлов как документов"""
    if not OPENAI_AVAILABLE or not openai_client or not message.document:
        return
    
    # Проверяем, что это аудиофайл
    filename = message.document.file_name or ""
    file_ext = get_file_extension(filename)
    if file_ext not in MODULE_CONFIG['supported_formats']:
        await message.reply(
            MESSAGES["send_audio"],
            reply_markup=get_back_menu()
        )
        return
    
    # Проверяем размер файла
    if message.document.file_size and message.document.file_size > MODULE_CONFIG['max_file_size']:
        size_mb = format_file_size(message.document.file_size)
        await message.reply(
            MESSAGES["file_too_large"].format(size=size_mb),
            reply_markup=get_back_menu()
        )
        return
    
    await process_audio_with_chatgpt(message, message.document.file_id, filename, message.document.file_size or 0)

async def process_audio_with_chatgpt(message: Message, file_id: str, filename: str, file_size: int):
    """Основная функция: транскрипция + ChatGPT"""
    start_time = time.time()
    
    # Этап 1: Показываем что обрабатываем аудио
    processing_msg = await message.reply(MESSAGES["processing_audio"])
    
    transcription_text = ""
    detected_language = "неизвестно"
    
    try:
        # Этап 2: Получаем файл от Telegram
        file_info = await message.bot.get_file(file_id)
        if not file_info.file_path:
            raise Exception("Не удалось получить путь к файлу")
        
        # Создаем временный файл
        file_ext = get_file_extension(filename)
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Скачиваем файл
            await message.bot.download_file(file_info.file_path, temp_path)
        
        # Этап 3: Транскрипция через Whisper
        await processing_msg.edit_text(MESSAGES["transcribing"])
        
        # Отправляем в Whisper API
        with open(temp_path, 'rb') as audio_file:
            language = MODULE_CONFIG['whisper_language'] if MODULE_CONFIG['whisper_language'] != 'auto' else None
            
            transcription = await asyncio.wait_for(
                asyncio.to_thread(
                    openai_client.audio.transcriptions.create,  # type: ignore
                    model=MODULE_CONFIG['whisper_model'],
                    file=audio_file,
                    language=language,
                    temperature=MODULE_CONFIG['whisper_temperature']
                ),
                timeout=MODULE_CONFIG['whisper_timeout']
            )
        
        # Удаляем временный файл
        os.unlink(temp_path)
        
        # Проверяем результат транскрипции
        if not transcription.text or transcription.text.strip() == "":
            await processing_msg.edit_text(
                MESSAGES["no_speech"],
                reply_markup=get_back_menu()
            )
            return
        
        transcription_text = transcription.text.strip()
        detected_language = getattr(transcription, 'language', 'неизвестно')
        
        # Этап 4: Отправляем в ChatGPT
        await processing_msg.edit_text(MESSAGES["chatgpt_thinking"])
        
        # Делаем запрос к ChatGPT API
        chatgpt_response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,  # type: ignore
                model=MODULE_CONFIG['chatgpt_model'],
                messages=[
                    {"role": "system", "content": MODULE_CONFIG['system_prompt']},
                    {"role": "user", "content": transcription_text}
                ],
                max_tokens=MODULE_CONFIG['chatgpt_max_tokens'],
                temperature=MODULE_CONFIG['chatgpt_temperature']
            ),
            timeout=MODULE_CONFIG['chatgpt_timeout']
        )
        
        # Получаем ответ ChatGPT
        ai_response = chatgpt_response.choices[0].message.content
        if ai_response:
            ai_response = ai_response.strip()
        else:
            ai_response = "Извините, не удалось получить ответ."
        
        # Подготавливаем финальный результат
        total_duration = round(time.time() - start_time, 1)
        file_size_mb = format_file_size(file_size)
        
        final_result = MESSAGES["final_result"].format(
            transcription=transcription_text,
            ai_response=ai_response,
            total_duration=total_duration,
            language=detected_language,
            file_size=file_size_mb
        )
        
        # Удаляем сообщение "Думаю..."
        await processing_msg.delete()
        
        # Отправляем финальный результат
        await message.reply(
            final_result,
            reply_markup=get_back_menu()
        )
        
    except asyncio.TimeoutError:
        await processing_msg.edit_text(
            MESSAGES["error_timeout"],
            reply_markup=get_back_menu()
        )
        
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except:
            pass
        
        error_text = str(e)
        
        # Определяем тип ошибки
        if transcription_text:
            # Ошибка на этапе ChatGPT
            await processing_msg.edit_text(
                MESSAGES["chatgpt_failed"].format(
                    transcription=transcription_text,
                    error=error_text
                ),
                reply_markup=get_back_menu()
            )
        elif "download" in error_text.lower():
            await processing_msg.edit_text(
                MESSAGES["error_download"].format(error=error_text),
                reply_markup=get_back_menu()
            )
        else:
            # Ошибка на этапе транскрипции
            await processing_msg.edit_text(
                MESSAGES["transcription_failed"].format(error=error_text),
                reply_markup=get_back_menu()
            )

@voice_assistant_router.message(StateFilter(VoiceAssistantStates.waiting_for_audio))
async def handle_non_audio_message(message: Message):
    """Обработка не-аудио сообщений в режиме голосового ассистента"""
    await message.reply(
        MESSAGES["send_audio"],
        reply_markup=get_back_menu()
    )

@voice_assistant_router.callback_query(F.data == "main_menu", StateFilter(VoiceAssistantStates.waiting_for_audio))
async def exit_voice_assistant_mode(callback: CallbackQuery, state: FSMContext):
    """Выход из режима голосового ассистента"""
    await state.clear()
    await callback.answer(MESSAGES["welcome_back"]) 