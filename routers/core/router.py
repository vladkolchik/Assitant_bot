from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from config import ALLOWED_USER_IDS
from messages import MESSAGES as GLOBAL_MESSAGES
from keyboards.main_menu import get_main_menu

core_router = Router()

@core_router.message(CommandStart())
async def start_cmd(message: Message):
    """Обработка команды /start"""
    if not message or not getattr(message, 'from_user', None):
        return
    from_user = message.from_user
    if not from_user or not hasattr(from_user, 'id'):
        return
    if from_user.id in ALLOWED_USER_IDS:
        await message.answer(GLOBAL_MESSAGES["start"], reply_markup=get_main_menu())
    else:
        await message.answer(GLOBAL_MESSAGES["no_access"])

@core_router.message(Command("menu"))
async def menu_cmd(message: Message):
    """Обработка команды /menu"""
    if not message or not getattr(message, 'from_user', None):
        return
    from_user = message.from_user
    if not from_user or not hasattr(from_user, 'id'):
        return
    if from_user.id in ALLOWED_USER_IDS:
        await message.answer("📋 Главное меню:", reply_markup=get_main_menu())
    else:
        await message.answer(GLOBAL_MESSAGES["no_access"])

@core_router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Возврат к главному меню"""
    if not callback.message:
        return
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())  # type: ignore
    await callback.answer() 