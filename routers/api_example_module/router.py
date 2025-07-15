from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from typing import cast
from .messages import MESSAGES
from .config import API_KEY, SERVICE_URL, IS_CONFIGURED

api_example_router = Router()

@api_example_router.callback_query(F.data == "api_example_mode")
async def activate_api_example(callback: CallbackQuery):
    """Активация демонстрационного API модуля"""
    
    if not callback.message:
        return
        
    # Проверяем конфигурацию модуля
    if not IS_CONFIGURED:
        await callback.message.edit_text(MESSAGES["not_configured"])  # type: ignore
        await callback.answer("Модуль не настроен!")
        return
    
    # Маскируем API ключ для показа (показываем первые 4 символа + ***)
    api_key_masked = f"{API_KEY[:4]}***" if API_KEY and len(API_KEY) > 4 else "***"
    
    # Показываем статус конфигурации
    config_message = MESSAGES["configured"].format(
        api_key_masked=api_key_masked,
        service_url=SERVICE_URL
    )
    
    # Создаем клавиатуру с действиями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Тест API", callback_data="api_test")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="api_settings")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(config_message, reply_markup=keyboard)  # type: ignore
    await callback.answer("API модуль готов!")

@api_example_router.callback_query(F.data == "api_test")
async def test_api_call(callback: CallbackQuery):
    """Демонстрация API вызова"""
    
    # В реальном модуле здесь был бы HTTP запрос
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(
    #         SERVICE_URL,
    #         headers={'Authorization': f'Bearer {API_KEY}'},
    #         timeout=MODULE_CONFIG['timeout']
    #     )
    
    await callback.message.edit_text(MESSAGES["demo_api_call"])
    await callback.answer("API вызов выполнен!")

@api_example_router.callback_query(F.data == "api_settings")
async def show_api_settings(callback: CallbackQuery):
    """Показ настроек модуля"""
    
    settings_text = f"""🔧 Настройки API модуля:

🔑 API ключ: {'✅ Настроен' if API_KEY else '❌ Не настроен'}
🌐 URL сервиса: {SERVICE_URL}
📁 Конфиг файл: routers/api_example_module/.env

Для изменения настроек отредактируйте .env файл модуля."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="api_example_mode")]
    ])
    
    await callback.message.edit_text(settings_text, reply_markup=keyboard)
    await callback.answer()

@api_example_router.message(F.text.contains("api"))
async def handle_api_mention(message: Message):
    """Реакция на упоминание 'api' в сообщениях"""
    await message.reply("🌐 Вы упомянули API! Попробуйте API Example модуль из меню.") 