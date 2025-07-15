from aiogram import Router
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram import F
# import logging

# logging.basicConfig(level=logging.INFO)

id_module_router = Router()

@id_module_router.callback_query(F.data == "id_mode")
async def handle_id_mode(callback_query: CallbackQuery):
    """Показ ID пользователя и чата через кнопку меню"""
    # logging.info("id_mode callback triggered")
    user_id = callback_query.from_user.id if callback_query.from_user else 'Unknown'
    chat_id = callback_query.message.chat.id if callback_query.message and callback_query.message.chat else 'Unknown'
    await callback_query.message.edit_text(f"🆔 **Ваши идентификаторы:**\n\n👤 ID пользователя: `{user_id}`\n💬 ID чата: `{chat_id}`", parse_mode="Markdown")  # type: ignore
    await callback_query.answer("ID получены!") 