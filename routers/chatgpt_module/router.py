"""
ChatGPT + Whisper модуль для Telegram бота
Интеграция с OpenAI API и поддержка аудио
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .config import MODULE_CONFIG, OPENAI_API_KEY
from .messages import MESSAGES
from .services import transcribe_voice_message, transcribe_video_note, transcribe_audio_file

# Состояния модуля
class ChatGPTStates(StatesGroup):
    waiting_for_message = State()

chatgpt_router = Router()

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

def get_token_params(model: str, max_tokens: int) -> dict:
    """
    Возвращает правильные параметры токенов для разных моделей OpenAI
    
    Reasoning-модели (o1, o3, o4 серии) используют max_completion_tokens
    Остальные модели используют max_tokens
    """
    # Reasoning-модели (o1, o3, o4 серии)
    if any(model.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']):
        return {'max_completion_tokens': max_tokens}
    # Все остальные модели (gpt-3.5-turbo, gpt-4, gpt-4o и т.д.)
    else:
        return {'max_tokens': max_tokens}

def get_api_params(model: str, messages: list, temperature: float, max_tokens: int, timeout: int) -> dict:
    """
    Формирует параметры для вызова OpenAI API с учетом особенностей модели
    
    Reasoning-модели (o1, o3, o4 серии) не поддерживают system сообщения и параметр temperature
    """
    base_params = {
        'model': model,
        'timeout': timeout
    }
    
    # Reasoning-модели имеют ограничения
    if any(model.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']):
        # Убираем system сообщения для reasoning-моделей (они не поддерживаются)
        user_messages = [msg for msg in messages if msg.get('role') != 'system']
        if not user_messages:
            # Если остались только system сообщения, берем последнее user сообщение
            user_messages = [{'role': 'user', 'content': messages[-1]['content']}]
        
        base_params.update({
            'messages': user_messages,
            **get_token_params(model, max_tokens)
            # temperature не поддерживается для reasoning-моделей
        })
    else:
        # Стандартные модели поддерживают все параметры
        base_params.update({
            'messages': messages,
            'temperature': temperature,
            **get_token_params(model, max_tokens)
        })
    
    return base_params

@chatgpt_router.callback_query(F.data == "chatgpt_mode")
async def activate_chatgpt(callback: CallbackQuery, state: FSMContext):
    """Активация режима ChatGPT"""
    if not callback.message:
        return
        
    if not OPENAI_AVAILABLE:
        await callback.message.edit_text(  # type: ignore
            MESSAGES["not_configured"], 
            reply_markup=get_back_menu()
        )
        await callback.answer("Модуль не настроен")
        return
    
    # Устанавливаем состояние ожидания сообщения
    await state.set_state(ChatGPTStates.waiting_for_message)
    
    await callback.message.edit_text(  # type: ignore
        MESSAGES["activation"],
        reply_markup=get_back_menu()
    )
    await callback.answer("🤖 ChatGPT активирован!")

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.text)
async def handle_chatgpt_message(message: Message, state: FSMContext):
    """Обработка текстовых сообщений для ChatGPT"""
    if not OPENAI_AVAILABLE or not openai_client or not message.text:
        return
    
    # Показываем что бот думает
    thinking_msg = await message.reply(MESSAGES["thinking"])
    
    try:
        # Формируем сообщения для API
        api_messages = [
            {"role": "system", "content": "Вы полезный AI ассистент. Отвечайте на русском языке, будьте дружелюбны и информативны."},
            {"role": "user", "content": message.text}
        ]
        
        # Получаем параметры для API с учетом модели
        api_params = get_api_params(
            model=MODULE_CONFIG['model'],
            messages=api_messages,
            temperature=MODULE_CONFIG['temperature'],
            max_tokens=MODULE_CONFIG['max_tokens'],
            timeout=MODULE_CONFIG['timeout']
        )
        
        # Делаем запрос к OpenAI API
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,  # type: ignore
            **api_params
        )
        
        # Получаем ответ
        ai_response = response.choices[0].message.content
        if ai_response:
            ai_response = ai_response.strip()
        else:
            ai_response = "Извините, не удалось получить ответ."
        
        # Удаляем сообщение "Думаю..."
        await thinking_msg.delete()
        
        # Отправляем ответ AI
        await message.reply(
            f"🤖 **ChatGPT:**\n\n{ai_response}",
            reply_markup=get_back_menu()
        )
        
    except asyncio.TimeoutError:
        await thinking_msg.edit_text(MESSAGES["error_timeout"])
        
    except Exception as e:
        error_text = MESSAGES["error_api"].format(error=str(e))
        await thinking_msg.edit_text(error_text)

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.voice)
async def handle_voice_message(message: Message, bot: Bot, state: FSMContext):
    """Обработка голосовых сообщений"""
    if not OPENAI_AVAILABLE or not openai_client or not message.voice:
        return
    
    # Показываем что обрабатываем аудио
    processing_msg = await message.reply(MESSAGES["processing_audio"])
    
    try:
        # Транскрибируем голосовое сообщение
        transcription, method, error = await transcribe_voice_message(bot, message.voice)
        
        if error:
            await processing_msg.edit_text(MESSAGES["audio_error"].format(error=error))
            return
        
        if not transcription:
            await processing_msg.edit_text(MESSAGES["no_speech_detected"])
            return
        
        # Обновляем сообщение - показываем что распознали
        await processing_msg.edit_text(MESSAGES["transcription_success"].format(
            method=method, 
            text=transcription[:100] + ("..." if len(transcription) > 100 else "")
        ))
        
        # Отправляем транскрипцию в ChatGPT
        await _process_transcribed_text(message, transcription, "🎤 Голосовое")
        
    except Exception as e:
        await processing_msg.edit_text(MESSAGES["audio_error"].format(error=str(e)))

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.video_note)
async def handle_video_note(message: Message, bot: Bot, state: FSMContext):
    """Обработка кружочков (видео заметок)"""
    if not OPENAI_AVAILABLE or not openai_client or not message.video_note:
        return
    
    # Показываем что обрабатываем аудио
    processing_msg = await message.reply(MESSAGES["processing_audio"])
    
    try:
        # Транскрибируем кружочек
        transcription, method, error = await transcribe_video_note(bot, message.video_note)
        
        if error:
            await processing_msg.edit_text(MESSAGES["audio_error"].format(error=error))
            return
        
        if not transcription:
            await processing_msg.edit_text(MESSAGES["no_speech_detected"])
            return
        
        # Обновляем сообщение - показываем что распознали
        await processing_msg.edit_text(MESSAGES["transcription_success"].format(
            method=method, 
            text=transcription[:100] + ("..." if len(transcription) > 100 else "")
        ))
        
        # Отправляем транскрипцию в ChatGPT
        await _process_transcribed_text(message, transcription, "⭕ Кружочек")
        
    except Exception as e:
        await processing_msg.edit_text(MESSAGES["audio_error"].format(error=str(e)))

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.audio)
async def handle_audio_file(message: Message, bot: Bot, state: FSMContext):
    """Обработка аудио файлов"""
    if not OPENAI_AVAILABLE or not openai_client or not message.audio:
        return
    
    # Показываем что обрабатываем аудио
    processing_msg = await message.reply(MESSAGES["processing_audio"])
    
    try:
        # Транскрибируем аудио файл
        transcription, method, error = await transcribe_audio_file(bot, message.audio)
        
        if error:
            await processing_msg.edit_text(MESSAGES["audio_error"].format(error=error))
            return
        
        if not transcription:
            await processing_msg.edit_text(MESSAGES["no_speech_detected"])
            return
        
        # Обновляем сообщение - показываем что распознали
        await processing_msg.edit_text(MESSAGES["transcription_success"].format(
            method=method, 
            text=transcription[:100] + ("..." if len(transcription) > 100 else "")
        ))
        
        # Отправляем транскрипцию в ChatGPT
        await _process_transcribed_text(message, transcription, "🎵 Аудио файл")
        
    except Exception as e:
        await processing_msg.edit_text(MESSAGES["audio_error"].format(error=str(e)))

async def _process_transcribed_text(message: Message, transcription: str, audio_type: str):
    """Обработка распознанного текста через ChatGPT"""
    # Показываем что ChatGPT думает
    thinking_msg = await message.reply(MESSAGES["thinking"])
    
    try:
        # Формируем сообщения для API
        api_messages = [
            {"role": "system", "content": "Вы полезный AI ассистент. Отвечайте на русском языке, будьте дружелюбны и информативны."},
            {"role": "user", "content": transcription}
        ]
        
        # Получаем параметры для API с учетом модели
        api_params = get_api_params(
            model=MODULE_CONFIG['model'],
            messages=api_messages,
            temperature=MODULE_CONFIG['temperature'],
            max_tokens=MODULE_CONFIG['max_tokens'],
            timeout=MODULE_CONFIG['timeout']
        )
        
        # Делаем запрос к OpenAI API
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,  # type: ignore
            **api_params
        )
        
        # Получаем ответ
        ai_response = response.choices[0].message.content
        if ai_response:
            ai_response = ai_response.strip()
        else:
            ai_response = "Извините, не удалось получить ответ."
        
        # Удаляем сообщение "Думаю..."
        await thinking_msg.delete()
        
        # Отправляем ответ с указанием источника
        response_text = f"{audio_type} → 🤖 **ChatGPT:**\n\n"
        response_text += f"*Распознано:* {transcription}\n\n"
        response_text += f"*Ответ:* {ai_response}"
        
        await message.reply(response_text, reply_markup=get_back_menu())
        
    except asyncio.TimeoutError:
        await thinking_msg.edit_text(MESSAGES["error_timeout"])
        
    except Exception as e:
        error_text = MESSAGES["error_api"].format(error=str(e))
        await thinking_msg.edit_text(error_text)

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message))
async def handle_unsupported_message(message: Message):
    """Обработка неподдерживаемых типов сообщений в режиме ChatGPT"""
    await message.reply(
        MESSAGES["unsupported_format"],
        reply_markup=get_back_menu()
    )

@chatgpt_router.callback_query(F.data == "main_menu", StateFilter(ChatGPTStates.waiting_for_message))
async def exit_chatgpt_mode(callback: CallbackQuery, state: FSMContext):
    """Выход из режима ChatGPT"""
    if not callback.message:
        return
    
    # Очищаем состояние
    await state.clear()
    
    # Импортируем главное меню
    from keyboards.main_menu import get_main_menu
    
    # Отображаем главное меню
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())  # type: ignore
    await callback.answer(MESSAGES["welcome_back"])

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.text.startswith("/chatgpt_info"))
async def show_module_info(message: Message):
    """Показать информацию о текущей конфигурации модуля"""
    current_model = MODULE_CONFIG['model']
    effective_tokens = MODULE_CONFIG['max_tokens']
    temperature = MODULE_CONFIG['temperature']
    
    # Определяем заметки и отображаемые токены для reasoning-моделей
    if any(current_model.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']):
        temp_note = "(игнорируется для reasoning)"
        token_note = f"(max_completion_tokens)"
        display_tokens = MODULE_CONFIG['max_completion_tokens']
    else:
        temp_note = ""
        token_note = "(max_tokens)"
        display_tokens = MODULE_CONFIG['original_max_tokens']
    
    info_text = MESSAGES["model_info"].format(
        model=current_model,
        temperature=temperature,
        temp_note=temp_note,
        max_tokens=display_tokens,
        token_note=token_note,
        whisper_mode=MODULE_CONFIG['whisper_mode'],
        whisper_language=MODULE_CONFIG['whisper_language'],
        max_size=MODULE_CONFIG['max_audio_size_mb'],
        max_duration=MODULE_CONFIG['max_audio_duration_sec'] // 60  # В минутах
    )
    
    await message.reply(info_text, reply_markup=get_back_menu())

@chatgpt_router.message(F.text.startswith("/chatgpt_info"))
async def show_module_info_outside(message: Message):
    """Показать информацию о модуле вне активного режима"""
    if not OPENAI_AVAILABLE:
        await message.reply(MESSAGES["not_configured"])
        return
        
    current_model = MODULE_CONFIG['model']
    effective_tokens = MODULE_CONFIG['max_tokens']
    temperature = MODULE_CONFIG['temperature']
    
    # Определяем заметки и отображаемые токены для reasoning-моделей
    if any(current_model.startswith(prefix) for prefix in ['o1-', 'o3-', 'o4-']):
        temp_note = "(игнорируется для reasoning)"
        token_note = f"(max_completion_tokens)"
        display_tokens = MODULE_CONFIG['max_completion_tokens']
    else:
        temp_note = ""
        token_note = "(max_tokens)"
        display_tokens = MODULE_CONFIG['original_max_tokens']
    
    info_text = MESSAGES["model_info"].format(
        model=current_model,
        temperature=temperature,
        temp_note=temp_note,
        max_tokens=display_tokens,
        token_note=token_note,
        whisper_mode=MODULE_CONFIG['whisper_mode'],
        whisper_language=MODULE_CONFIG['whisper_language'],
        max_size=MODULE_CONFIG['max_audio_size_mb'],
        max_duration=MODULE_CONFIG['max_audio_duration_sec'] // 60  # В минутах
    )
    
    info_text += f"\n\n💡 Активируйте модуль: /start → 🤖 ChatGPT"
    
    await message.reply(info_text) 