from aiogram import Router, types
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from config import ALLOWED_USER_IDS, FROM_EMAIL, DEFAULT_RECIPIENT
from messages import MESSAGES
from services.email_sender import send_email_oauth2
from keyboards.email_ui import get_main_menu, get_email_menu, get_recipient_menu
import re
import asyncio

email_router = Router()

user_states = {}
default_recipient = DEFAULT_RECIPIENT

def is_valid_email(email):
    return re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", email)

@email_router.message(CommandStart())
async def start_cmd(message: Message):
    if message.from_user.id in ALLOWED_USER_IDS:
        user_states[message.from_user.id] = {"mode": "default", "recipient": None, "draft": {}, "files": []}
        await message.answer(MESSAGES["start"], reply_markup=get_main_menu())
    else:
        await message.answer(MESSAGES["no_access"])

@email_router.message(Command("menu"))
async def menu_cmd(message: Message):
    if message.from_user.id in ALLOWED_USER_IDS:
        user_id = message.from_user.id
        
        # Инициализируем состояние если его нет, но сохраняем существующие данные
        if user_id not in user_states:
            user_states[user_id] = {"mode": "default", "recipient": None, "draft": {}, "files": []}
        else:
            # Выходим из режима отправки писем, но сохраняем черновики и получателя
            user_states[user_id]["mode"] = "default"
        
        await message.answer(MESSAGES["start"], reply_markup=get_main_menu())
    else:
        await message.answer(MESSAGES["no_access"])

@email_router.callback_query()
async def menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    state = user_states.get(user_id)

    if data == "email_mode":
        state["mode"] = "email"
        # НЕ сбрасываем файлы при входе в email режим, сохраняем черновик
        
        # Формируем динамическое сообщение с информацией о состоянии
        recipient = state["recipient"] or default_recipient
        files_count = len(state.get("files", []))
        
        msg = MESSAGES["enter_email_mode"]
        msg += "\n\n" + "─" * 30
        msg += f"\n📧 <b>Получатель:</b> {recipient}"
        msg += f"\n🗂 <b>Файлов в черновике:</b> {files_count}"
        
        if files_count > 0:
            msg += " ⚠️"
        
        try:
            await callback.message.edit_text(msg, reply_markup=get_email_menu())
        except TelegramBadRequest:
            await callback.answer("ℹ️ Уже в режиме email", show_alert=False)
    elif data == "reset_draft":
        state["draft"] = {}
        state["files"] = []
        await callback.message.edit_text("🗑 Черновик и вложения очищены.", reply_markup=get_email_menu())
    elif data == "exit_email_mode":
        state["mode"] = "default"
        # НЕ сбрасываем черновик и файлы при выходе из email режима
        await callback.message.edit_text(MESSAGES["exit_email_mode"], reply_markup=get_main_menu())
    elif data == "recipient_menu":
        current = state["recipient"] or default_recipient
        msg = f"🔧 Управление получателем:\n\n📨 Текущий получатель: <b>{current}</b>"
        
        try:
            await callback.message.edit_text(msg, reply_markup=get_recipient_menu(), parse_mode='HTML')
        except TelegramBadRequest:
            await callback.answer("ℹ️ Получатель не изменился", show_alert=False)

    elif data == "edit_recipient":
        state["mode"] = "entering_email"
        await callback.message.edit_text(MESSAGES["ask_recipient"], reply_markup=get_recipient_menu())
    elif data == "reset_recipient":
        state["recipient"] = None
        await callback.message.edit_text(MESSAGES["recipient_reset"], reply_markup=get_recipient_menu())
    elif data == "back_to_email_menu":
        # Формируем динамическое сообщение с информацией о состоянии
        recipient = state["recipient"] or default_recipient
        files_count = len(state.get("files", []))
        
        msg = MESSAGES["enter_email_mode"]
        msg += "\n\n" + "─" * 30
        msg += f"\n📧 <b>Получатель:</b> {recipient}"
        msg += f"\n🗂 <b>Файлов в черновике:</b> {files_count}"
        
        if files_count > 0:
            msg += " ⚠️"
        
        await callback.message.edit_text(msg, reply_markup=get_email_menu(), parse_mode='HTML')
    elif data == "show_attachments":
        files = state.get("files", [])
        if not files:
            msg = "📎 Вложения не найдены."
        else:
            msg = f"📎 Вложения ({len(files)}):\n" + "\n".join([f"- {f[0]}" for f in files])
        
        try:
            await callback.message.edit_text(msg, reply_markup=get_email_menu())
        except TelegramBadRequest:
            await callback.answer("ℹ️ Информация актуальна", show_alert=False)

    user_states[user_id] = state
    await callback.answer()

@email_router.message()
async def handle_input(message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        await message.answer(MESSAGES["no_access"])
        return

    state = user_states.get(user_id)
    text = message.text.strip() if message.text else ""

    if state["mode"] == "entering_email":
        if is_valid_email(text):
            state["recipient"] = text
            state["mode"] = "email"
            await message.answer(MESSAGES["recipient_saved"].format(email=text), reply_markup=get_email_menu())
        else:
            await message.answer(MESSAGES["invalid_email"])
    elif state["mode"] == "email":
        if message.document:
            file = await message.bot.download(message.document)
            file_bytes = file.read()
            if message.caption:
                lines = message.caption.strip().splitlines()
                if len(lines) >= 2:
                    # Ждем 2 секунды для накопления файлов из групповых сообщений
                    await asyncio.sleep(2)
                    
                    subject = lines[0]
                    body = "\n".join(lines[1:])
                    recipient = state["recipient"] or default_recipient
                    attachments = state["files"] + [(message.document.file_name, file_bytes)]
                    success = send_email_oauth2(recipient, subject, body, attachments)
                    if success:
                        await message.answer("✅ Письмо с вложением отправлено.")
                    else:
                        await message.answer(MESSAGES["email_failed"])
                    state["draft"] = {}
                    state["files"] = []
                    user_states[user_id] = state
                    return
                else:
                    await message.answer(MESSAGES["invalid_format"])
                    return
            else:
                state["files"].append((message.document.file_name, file_bytes))
                await message.answer(f"📎 Файл «{message.document.file_name}» прикреплён.")
        elif message.photo:
            # Берем фото с наивысшим качеством (последнее в массиве)
            photo = message.photo[-1]
            file = await message.bot.download(photo)
            file_bytes = file.read()
            file_name = f"screenshot_{photo.file_unique_id}.jpg"
            
            if message.caption:
                lines = message.caption.strip().splitlines()
                if len(lines) >= 2:
                    # Ждем 2 секунды для накопления файлов из групповых сообщений
                    await asyncio.sleep(2)
                    
                    subject = lines[0]
                    body = "\n".join(lines[1:])
                    recipient = state["recipient"] or default_recipient
                    attachments = state["files"] + [(file_name, file_bytes)]
                    success = send_email_oauth2(recipient, subject, body, attachments)
                    if success:
                        await message.answer("✅ Письмо с изображением отправлено.")
                    else:
                        await message.answer(MESSAGES["email_failed"])
                    state["draft"] = {}
                    state["files"] = []
                    user_states[user_id] = state
                    return
                else:
                    await message.answer(MESSAGES["invalid_format"])
                    return
            else:
                state["files"].append((file_name, file_bytes))
                await message.answer(f"📎 Изображение «{file_name}» прикреплено.")
        elif not state["draft"] and message.text:
            lines = text.splitlines()
            if len(lines) >= 2:
                # Ждем 2 секунды для накопления файлов из групповых сообщений
                await asyncio.sleep(2)
                
                subject = lines[0]
                body = "\n".join(lines[1:])
                recipient = state["recipient"] or default_recipient
                success = send_email_oauth2(recipient, subject, body, state["files"])
                if success:
                    if state["files"]:
                        await message.answer("✅ Письмо с вложением отправлено.")
                    else:
                        await message.answer("✅ Письмо отправлено.")
                else:
                    await message.answer(MESSAGES["email_failed"])
                state["draft"] = {}
                state["files"] = []
            else:
                await message.answer(MESSAGES["invalid_format"])
        else:
            await message.answer("Вы уже отправили письмо или начали новое. Используйте Меню, чтобы выйти или сбросить.")

    else:
        await message.answer(f"Вы сказали: {text}")

    user_states[user_id] = state
