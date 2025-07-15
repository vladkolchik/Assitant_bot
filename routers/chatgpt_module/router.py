"""
ChatGPT модуль для Telegram бота
Интеграция с OpenAI API
"""
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .config import MODULE_CONFIG, OPENAI_API_KEY
from .messages import MESSAGES

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
    """Обработка сообщений для ChatGPT"""
    if not OPENAI_AVAILABLE or not openai_client or not message.text:
        return
    
    # Показываем что бот думает
    thinking_msg = await message.reply(MESSAGES["thinking"])
    
    try:
        # Делаем запрос к OpenAI API
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,  # type: ignore
            model=MODULE_CONFIG['model'],
            messages=[
                {"role": "system", "content": "Вы полезный AI ассистент. Отвечайте на русском языке, будьте дружелюбны и информативны."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=MODULE_CONFIG['max_tokens'],
            temperature=MODULE_CONFIG['temperature'],
            timeout=MODULE_CONFIG['timeout']
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

@chatgpt_router.message(StateFilter(ChatGPTStates.waiting_for_message))
async def handle_non_text_message(message: Message):
    """Обработка не-текстовых сообщений в режиме ChatGPT"""
    await message.reply(
        "🤖 Я понимаю только текстовые сообщения.\nОтправьте текст для общения с ChatGPT.",
        reply_markup=get_back_menu()
    )

@chatgpt_router.callback_query(F.data == "main_menu", StateFilter(ChatGPTStates.waiting_for_message))
async def exit_chatgpt_mode(callback: CallbackQuery, state: FSMContext):
    """Выход из режима ChatGPT"""
    await state.clear()
    await callback.answer(MESSAGES["welcome_back"]) 