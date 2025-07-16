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
from .image_utils import create_image_processor
from .memory_service import memory_service

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

# Инициализируем обработчик изображений
try:
    if MODULE_CONFIG['vision_enabled']:
        image_processor = create_image_processor(MODULE_CONFIG)
        VISION_AVAILABLE = True
    else:
        image_processor = None
        VISION_AVAILABLE = False
except ImportError:
    print("⚠️ PIL (Pillow) library not installed. Vision API disabled. Run: pip install Pillow")
    image_processor = None
    VISION_AVAILABLE = False

async def toggle_mem0_setting() -> bool:
    """
    Переключает MEM0_ENABLED в .env файле модуля
    Возвращает новое состояние (True/False)
    """
    try:
        import os
        import re
        from pathlib import Path
        
        env_file = Path(__file__).parent / '.env'
        
        if env_file.exists():
            content = env_file.read_text(encoding='utf-8')
        else:
            content = ""
        
        # Ищем строку MEM0_ENABLED
        if 'MEM0_ENABLED=' in content:
            # Переключаем значение
            if 'MEM0_ENABLED=true' in content:
                new_content = content.replace('MEM0_ENABLED=true', 'MEM0_ENABLED=false')
                new_value = False
            else:
                new_content = content.replace('MEM0_ENABLED=false', 'MEM0_ENABLED=true')
                new_value = True
        else:
            # Добавляем настройку если её нет
            new_content = content + '\n# Mem0 долговременная память\nMEM0_ENABLED=false\n'
            new_value = False
        
        # Сохраняем изменения
        env_file.write_text(new_content, encoding='utf-8')
        
        # Обновляем конфигурацию модуля в runtime
        MODULE_CONFIG['mem0_enabled'] = new_value
        
        return new_value
        
    except Exception as e:
        print(f"❌ Ошибка переключения MEM0_ENABLED: {e}")
        return MODULE_CONFIG.get('mem0_enabled', False)

def get_back_menu():
    """Клавиатура для возврата в главное меню и управления гибридной памятью"""
    keyboard = []
    
    # Первый ряд: кнопки управления памятью
    memory_row = []
    
    # Кнопка переключения режима памяти
    if MODULE_CONFIG.get('mem0_enabled', False):
        memory_row.append(InlineKeyboardButton(text="🔥➡️📝 Только сессионная", callback_data="toggle_memory_mode"))
    else:
        memory_row.append(InlineKeyboardButton(text="📝➡️🔥 Включить гибридный", callback_data="toggle_memory_mode"))
    
    # Кнопка очистки памяти (всегда доступна)
    memory_row.append(InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_memory"))
    
    keyboard.append(memory_row)
    
    # Второй ряд: информация о текущем режиме памяти
    memory_stats = memory_service.get_memory_stats()
    if memory_stats.get('mode') == 'hybrid':
        keyboard.append([InlineKeyboardButton(text="🔥 Режим: Гибридная память (Mem0 + RAM)", callback_data="memory_info")])
    else:
        keyboard.append([InlineKeyboardButton(text="📝 Режим: Сессионная память (RAM)", callback_data="memory_info")])
    
    # Третий ряд: возврат в главное меню
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
    
    if not message.from_user:
        return
        
    user_id = str(message.from_user.id)
    user_text = message.text
    
    # Показываем что бот думает
    thinking_msg = await message.reply(MESSAGES["thinking"])
    
    try:
        # Получаем полный контекст из гибридной системы памяти
        memory_context, context_count, context_source = await memory_service.get_full_context(user_id, user_text)
        
        # print(f"🔍 ОТЛАДКА - Контекст из {context_source} памяти: {context_count} элементов")
        # print(f"🔍 ОТЛАДКА - Загруженный контекст: {memory_context}")
        
        # Формируем сообщения для API
        system_content = "Вы полезный AI ассистент. Отвечайте на русском языке, будьте дружелюбны и информативны."
        
        # Для reasoning-моделей добавляем контекст в пользовательское сообщение
        user_content = user_text
        if memory_context:
            user_content = f"Контекст из предыдущих диалогов:\n{memory_context}\n\nВопрос пользователя: {user_text}"
        
        api_messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
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
        
        # Формируем ответ с информацией о памяти
        response_text = f"🤖 **ChatGPT:**\n\n{ai_response}"
        
        # Добавляем информацию о загруженном контексте если есть
        if context_count > 0:
            if context_source == "гибридной":
                response_text += f"\n\n🔥 *Загружен контекст из гибридной памяти: {context_count} элементов*"
            elif context_source == "сессионной":
                response_text += f"\n\n📝 *Загружен контекст из сессионной памяти: {context_count} диалогов*"
        
        # Отправляем ответ AI
        await message.reply(response_text, reply_markup=get_back_menu())
        
        # Сохраняем диалог в гибридную память
        try:
            await memory_service.save_conversation(user_id, user_text, ai_response)
            # print(f"💾 ОТЛАДКА - Сохранен диалог в {context_source} память")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в память: {e}")
        
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

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message), F.photo)
async def handle_image_message(message: Message, bot: Bot, state: FSMContext):
    """Обработка изображений через Vision API"""
    if not OPENAI_AVAILABLE or not openai_client or not message.photo:
        return
    
    if not VISION_AVAILABLE or not image_processor:
        await message.reply(
            "📷 **Vision API отключен или недоступен**\n\n"
            "Возможные причины:\n"
            "• Модуль не настроен для работы с изображениями\n"
            "• Модель не поддерживает Vision API\n"
            "• Отсутствует библиотека PIL\n\n"
            f"Используйте модели: gpt-4o, gpt-4o-mini, gpt-4-vision-preview",
            reply_markup=get_back_menu()
        )
        return
    
    # Показываем что обрабатываем изображение
    processing_msg = await message.reply("🖼️ Обрабатываю изображение...")
    
    try:
        # Берем изображение наивысшего качества
        photo = message.photo[-1]
        
        # Загружаем изображение
        file_stream = await bot.download(photo)  # type: ignore
        if not file_stream:
            await processing_msg.edit_text("❌ Не удалось загрузить изображение")
            return
        
        image_bytes = file_stream.read()  # type: ignore
        file_stream.close()
        
        # Подготавливаем изображение для API
        base64_image, image_info = image_processor.prepare_image_for_api(
                            image_bytes, MODULE_CONFIG['vision_quality']
        )
        
        # Показываем информацию о затратах (если включено)
        if MODULE_CONFIG['vision_cost_warnings']:
            cost_warning = image_processor.get_cost_warning(image_info, MODULE_CONFIG['model'])
            await processing_msg.edit_text(
                f"🖼️ **Изображение обработано:**\n\n{cost_warning}\n\n🤖 Анализирую..."
            )
        else:
            await processing_msg.edit_text("🤖 Анализирую изображение...")
        
        # Формируем сообщения для Vision API
        user_text = message.caption if message.caption else "Опишите, что вы видите на этом изображении."
        
        api_messages = [
            {
                "role": "system", 
                "content": "Вы полезный AI ассистент с возможностью анализа изображений. Отвечайте на русском языке, будьте дружелюбны и подробны в описаниях."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": MODULE_CONFIG['vision_quality']
                        }
                    }
                ]
            }
        ]
        
        # Получаем параметры для API с учетом модели (без temperature для reasoning моделей)
        api_params = get_api_params(
            model=MODULE_CONFIG['model'],
            messages=api_messages,
            temperature=MODULE_CONFIG['temperature'],
            max_tokens=MODULE_CONFIG['max_tokens'],
            timeout=MODULE_CONFIG['timeout']
        )
        
        # Делаем запрос к Vision API
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,  # type: ignore
            **api_params
        )
        
        # Получаем ответ
        ai_response = response.choices[0].message.content
        if ai_response:
            ai_response = ai_response.strip()
        else:
            ai_response = "Извините, не удалось проанализировать изображение."
        
        # Удаляем сообщение обработки
        await processing_msg.delete()
        
        # Формируем итоговый ответ
        response_text = f"🖼️ **Vision API:**\n\n"
        if message.caption:
            response_text += f"*Ваш вопрос:* {message.caption}\n\n"
        response_text += f"*Анализ изображения:* {ai_response}"
        
        # Добавляем информацию о затратах в конце (если включено)
        if MODULE_CONFIG['vision_cost_warnings']:
            estimated_cost = image_processor.estimate_cost_usd(image_info['estimated_tokens'], MODULE_CONFIG['model'])
            response_text += f"\n\n💰 *Затрачено: ~${estimated_cost:.4f} (~{image_info['estimated_tokens']} токенов)*"
        
        await message.reply(response_text, reply_markup=get_back_menu())
        
    except Exception as e:
        error_text = f"❌ **Ошибка Vision API:**\n{str(e)}\n\n💡 Возможные причины:\n• Модель не поддерживает изображения\n• Превышен лимит API\n• Проблемы с обработкой изображения"
        await processing_msg.edit_text(error_text)

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message))
async def handle_unsupported_message(message: Message):
    """Обработка неподдерживаемых типов сообщений в режиме ChatGPT"""
    await message.reply(
        MESSAGES["unsupported_format"],
        reply_markup=get_back_menu()
    )

@chatgpt_router.callback_query(F.data == "clear_memory", StateFilter(ChatGPTStates.waiting_for_message))
async def clear_user_memory(callback: CallbackQuery):
    """Очистка всей памяти пользователя (долговременной и сессионной)"""
    if not callback.message:
        return
    
    user_id = str(callback.from_user.id)
    
    try:
        # Очищаем всю память пользователя в гибридной системе
        success = await memory_service.clear_all_memory(user_id)
        
        if success:
            await callback.message.edit_text(  # type: ignore
                MESSAGES["memory_cleared"],
                reply_markup=get_back_menu()
            )
            await callback.answer("🗑️ Память очищена!")
        else:
            await callback.message.edit_text(  # type: ignore
                MESSAGES["memory_clear_error"],
                reply_markup=get_back_menu()
            )
            await callback.answer("❌ Ошибка очистки")
            
    except Exception as e:
        print(f"❌ Ошибка очистки памяти: {e}")
        await callback.message.edit_text(  # type: ignore
            MESSAGES["memory_clear_error"],
            reply_markup=get_back_menu()
        )
        await callback.answer("❌ Ошибка очистки")

@chatgpt_router.callback_query(F.data == "toggle_memory_mode", StateFilter(ChatGPTStates.waiting_for_message))
async def toggle_memory_mode(callback: CallbackQuery):
    """Переключение режима памяти (гибридная ⇄ сессионная)"""
    if not callback.message:
        return
    
    try:
        # Переключаем режим памяти
        new_mem0_state = await toggle_mem0_setting()
        
        if new_mem0_state:
            mode_name = "гибридную память (Mem0 + RAM)"
            icon = "🔥"
            description = "Теперь используется максимальный контекст: семантический поиск по всей истории + последние диалоги."
        else:
            mode_name = "сессионную память (RAM)"
            icon = "📝"
            description = "Теперь используется только память текущей сессии: последние диалоги в оперативной памяти."
        
        await callback.message.edit_text(  # type: ignore
            f"🔄 **Режим памяти изменен**\n\n{icon} Переключено на {mode_name}\n\n💡 **Описание:**\n{description}\n\n🔧 **Подсказка:** Переключение влияет только на новые сообщения. Существующий контекст сохраняется.",
            reply_markup=get_back_menu()
        )
        await callback.answer(f"{icon} Переключено на {mode_name}")
        
    except Exception as e:
        print(f"❌ Ошибка переключения режима памяти: {e}")
        await callback.answer("❌ Ошибка переключения режима")

@chatgpt_router.callback_query(F.data == "memory_info", StateFilter(ChatGPTStates.waiting_for_message))
async def show_memory_info(callback: CallbackQuery):
    """Показать подробную информацию о текущем режиме памяти"""
    if not callback.message:
        return
    
    try:
        memory_stats = memory_service.get_memory_stats()
        mode = memory_stats.get('mode', 'unknown')
        
        if mode == 'hybrid':
            # Гибридный режим
            user_id = str(callback.from_user.id)
            session_stats = memory_service.get_session_memory_stats(user_id)
            
            info_text = f"🔥 **Гибридная память (Mem0 + RAM)**\n\n"
            info_text += f"**Статус:** ✅ Активна\n"
            info_text += f"**Долговременная память:** Mem0 API\n"
            info_text += f"**Сессионная память:** {session_stats['messages_count']}/{session_stats['max_capacity']} диалогов\n\n"
            info_text += f"**Как работает:**\n"
            info_text += f"• 🧠 Семантический поиск по всей истории (Mem0)\n"
            info_text += f"• 📝 Последние диалоги текущей сессии (RAM)\n"
            info_text += f"• 🔀 Объединение обоих контекстов для максимальной эффективности\n\n"
            info_text += f"**Преимущества:**\n"
            info_text += f"• Максимально полный контекст\n"
            info_text += f"• Персонализация на основе всей истории\n"
            info_text += f"• Понимание как долгосрочных, так и текущих тем"
        else:
            # Сессионная память
            user_id = str(callback.from_user.id)
            session_stats = memory_service.get_session_memory_stats(user_id)
            
            info_text = f"📝 **Сессионная память (RAM)**\n\n"
            info_text += f"**Статус:** ✅ Активна\n"
            info_text += f"**Хранение:** Локальная память\n"
            info_text += f"**Диалогов:** {session_stats['messages_count']}/{session_stats['max_capacity']}\n"
            info_text += f"**Время жизни:** До перезапуска бота\n\n"
            info_text += f"**Как работает:**\n"
            info_text += f"• 💾 Хранит последние {session_stats['max_capacity']} пар диалогов\n"
            info_text += f"• ⚡ Быстрый доступ к недавней истории\n"
            info_text += f"• 🆓 Полностью бесплатная\n\n"
            info_text += f"**Для максимального эффекта включите гибридный режим! 🔥**"
        
        await callback.message.edit_text(  # type: ignore
            info_text,
            reply_markup=get_back_menu()
        )
        await callback.answer("ℹ️ Информация о памяти")
        
    except Exception as e:
        print(f"❌ Ошибка получения информации о памяти: {e}")
        await callback.answer("❌ Ошибка получения информации")

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
    
    # Добавляем информацию о гибридной системе памяти
    memory_stats = memory_service.get_memory_stats()
    user_id = str(message.from_user.id) if message.from_user else "unknown"
    session_stats = memory_service.get_session_memory_stats(user_id)
    
    if memory_stats.get('mode') == 'hybrid':
        info_text += f"\n\n**🔥 Гибридная память (Mem0 + RAM):**\n"
        info_text += f"• Статус: ✅ Активна\n"
        info_text += f"• Долговременная: Mem0 API\n"
        info_text += f"• Сессионная: {session_stats['messages_count']}/{session_stats['max_capacity']} диалогов\n"
        info_text += f"• Максимальный контекст из обеих систем"
    else:
        info_text += f"\n\n**📝 Сессионная память (RAM):**\n"
        info_text += f"• Статус: ✅ Активна\n"
        info_text += f"• Диалогов: {session_stats['messages_count']}/{session_stats['max_capacity']}\n"
        info_text += f"• Только текущая сессия"
    
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
    
    # Информация о Vision API для внешнего вызова
    vision_status = "✅ Включен" if MODULE_CONFIG['vision_enabled'] and VISION_AVAILABLE else "❌ Отключен"
    vision_quality = MODULE_CONFIG['vision_quality'] if MODULE_CONFIG['vision_enabled'] else "N/A"
    
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
    
    # Добавляем информацию о Vision API
    info_text += f"\n\n**Vision API (изображения):**\n"
    info_text += f"• Статус: {vision_status}\n"
    info_text += f"• Качество: {vision_quality}\n"
    info_text += f"• Макс. размер: {MODULE_CONFIG['max_image_size_mb']} МБ\n"
    info_text += f"• Предупреждения о затратах: {'✅' if MODULE_CONFIG['vision_cost_warnings'] else '❌'}"
    
    # Добавляем информацию о гибридной системе памяти
    memory_stats = memory_service.get_memory_stats()
    
    if memory_stats.get('mode') == 'hybrid':
        info_text += f"\n\n**🔥 Гибридная память (Mem0 + RAM):**\n"
        info_text += f"• Статус: ✅ Активна\n"
        info_text += f"• Долговременная: Mem0 API (семантический поиск)\n"
        info_text += f"• Сессионная: Последние диалоги в RAM\n"
        info_text += f"• Максимальный контекст из обеих систем"
    else:
        info_text += f"\n\n**📝 Сессионная память (RAM):**\n"
        info_text += f"• Статус: ✅ Доступна\n"
        info_text += f"• Хранение: Локальное во время сессии\n"
        info_text += f"• Для максимального эффекта: настройте MEM0_API_KEY в .env"
    
    info_text += f"\n\n💡 Активируйте модуль: /start → 🤖 ChatGPT"
    
    await message.reply(info_text) 