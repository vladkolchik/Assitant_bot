from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from .messages import MESSAGES
import datetime

test_module_router = Router()

@test_module_router.callback_query(F.data == "test_mode")
async def test_callback(callback: CallbackQuery):
    """Обработка кнопки тестового модуля из главного меню"""
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    await callback.message.answer(
        f"{MESSAGES['test_activated']}\n"
        f"⏰ Время: {current_time}\n"
        f"👤 Пользователь: {callback.from_user.first_name}\n"
        f"🆔 ID: {callback.from_user.id}"
    )
    await callback.answer("Тестовый модуль активирован! ✅")

@test_module_router.message(F.text.contains("тест"))
async def test_message(message: Message):
    """Реагирует на сообщения содержащие слово 'тест'"""
    await message.answer(MESSAGES["test_message"])

@test_module_router.message(F.text == "🧪")
async def test_emoji(message: Message):
    """Реагирует на эмодзи пробирки"""
    await message.answer(MESSAGES["test_emoji"]) 