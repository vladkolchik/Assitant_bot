from aiogram import Router
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram import F
# import logging

# logging.basicConfig(level=logging.INFO)

id_module_router = Router()

@id_module_router.message()
async def send_user_id(message: Message):
    user_id = message.from_user.id if message.from_user else 'Unknown'
    await message.answer(f"Ваш ID: {user_id}")

@id_module_router.message()
async def send_chat_id(message: Message):
    chat_id = message.chat.id if message.chat else 'Unknown'
    await message.answer(f"ID чата: {chat_id}")

@id_module_router.callback_query(F.data == "id_mode")
async def handle_id_mode(callback_query: CallbackQuery):
    # logging.info("id_mode callback triggered")
    user_id = callback_query.from_user.id if callback_query.from_user else 'Unknown'
    chat_id = callback_query.message.chat.id if callback_query.message and callback_query.message.chat else 'Unknown'
    await callback_query.message.answer(f"Ваш ID: {user_id}\nID чата: {chat_id}")
    await callback_query.answer() 