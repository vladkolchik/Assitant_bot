from aiogram import Router, types
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from config import ALLOWED_USER_IDS
from .config import GMAIL_ADDRESS, DEFAULT_EMAIL_RECIPIENT
from .messages import MESSAGES  # локальные сообщения
from messages import MESSAGES as GLOBAL_MESSAGES  # глобальные сообщения
from .services import send_email_oauth2, get_auth_status, is_authorized
from .keyboards import get_email_menu, get_recipient_menu
import re
import asyncio
from aiogram import F

email_router = Router()

user_states = {}
default_recipient = DEFAULT_EMAIL_RECIPIENT

def is_valid_email(email):
    return re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", email)

# Команды /start и /menu перенесены в core модуль для лучшей архитектуры

@email_router.callback_query(F.data.in_({
    "email_mode", "reset_draft", "exit_email_mode", "recipient_menu", 
    "edit_recipient", "reset_recipient", "back_to_email_menu", "show_attachments"
}))
async def menu_handler(callback: CallbackQuery):
    if not callback or not getattr(callback, 'from_user', None):
        return
    from_user = callback.from_user
    if not from_user or not hasattr(from_user, 'id'):
        return
    user_id = from_user.id
    data = callback.data
    if user_id not in user_states or "email_router" not in user_states[user_id]:
        user_states[user_id] = {}
        user_states[user_id]["email_router"] = {"mode": "default", "recipient": None, "draft": {}, "files": []}
    state = user_states[user_id]["email_router"]

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
            if callback.message:
                await callback.message.edit_text(msg, reply_markup=get_email_menu())  # type: ignore
        except TelegramBadRequest:
            await callback.answer("ℹ️ Уже в режиме email", show_alert=False)
    elif data == "reset_draft":
        state["draft"] = {}
        state["files"] = []
        if callback.message:
            await callback.message.edit_text("🗑 Черновик и вложения очищены.", reply_markup=get_email_menu())  # type: ignore
    elif data == "exit_email_mode":
        state["mode"] = "default"
        # НЕ сбрасываем черновик и файлы при выходе из email режима
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        back_to_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        if callback.message:
            await callback.message.edit_text(MESSAGES["exit_email_mode"], reply_markup=back_to_menu)  # type: ignore
    elif data == "recipient_menu":
        current = state["recipient"] or default_recipient
        msg = f"🔧 Управление получателем:\n\n📨 Текущий получатель: <b>{current}</b>"
        
        try:
            if callback.message:
                await callback.message.edit_text(msg, reply_markup=get_recipient_menu(), parse_mode='HTML')  # type: ignore
        except TelegramBadRequest:
            await callback.answer("ℹ️ Получатель не изменился", show_alert=False)

    elif data == "edit_recipient":
        state["mode"] = "entering_email"
        if callback.message:
            await callback.message.edit_text(MESSAGES["ask_recipient"], reply_markup=get_recipient_menu())  # type: ignore
    elif data == "reset_recipient":
        state["recipient"] = None
        if callback.message:
            await callback.message.edit_text(MESSAGES["recipient_reset"], reply_markup=get_recipient_menu())  # type: ignore
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
        
        if callback.message:
            await callback.message.edit_text(msg, reply_markup=get_email_menu(), parse_mode='HTML')  # type: ignore
    elif data == "show_attachments":
        files = state.get("files", [])
        if not files:
            msg = "📎 Вложения не найдены."
        else:
            msg = f"📎 Вложения ({len(files)}):\n" + "\n".join([f"- {f[0]}" for f in files])
        
        try:
            if callback.message:
                await callback.message.edit_text(msg, reply_markup=get_email_menu())  # type: ignore
        except TelegramBadRequest:
            await callback.answer("ℹ️ Информация актуальна", show_alert=False)

    user_states[user_id]["email_router"] = state
    await callback.answer()

@email_router.message()
async def handle_input(message: Message):
    if not message or not getattr(message, 'from_user', None):
        return
    from_user = message.from_user
    if not from_user or not hasattr(from_user, 'id'):
        return
    user_id = from_user.id
    if user_id not in ALLOWED_USER_IDS:
        await message.answer(GLOBAL_MESSAGES["no_access"])
        return
    if user_id not in user_states or "email_router" not in user_states[user_id]:
        user_states[user_id] = {}
        user_states[user_id]["email_router"] = {"mode": "default", "recipient": None, "draft": {}, "files": []}
    state = user_states[user_id]["email_router"]

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
            try:
                # Безопасная загрузка файла из Telegram
                if message.bot and message.document:
                    file_stream = await message.bot.download(message.document)  # type: ignore
                    if file_stream:
                        file_bytes = file_stream.read()  # type: ignore  # Читаем все байты
                        file_stream.close()  # Закрываем поток
                        file_name = message.document.file_name or f"document_{message.document.file_unique_id}"
                    else:
                        await message.answer("❌ Не удалось загрузить файл")
                        return
                else:
                    await message.answer("❌ Ошибка: отсутствует бот или документ")
                    return
            except Exception as e:
                await message.answer(f"❌ Ошибка загрузки файла: {e}")
                return
            
            if message.caption:
                lines = message.caption.strip().splitlines()
                if len(lines) >= 2:
                    # Ждем 2 секунды для накопления файлов из групповых сообщений
                    await asyncio.sleep(2)
                    
                    subject = lines[0]
                    body = "\n".join(lines[1:])
                    recipient = state["recipient"] or default_recipient
                    attachments = state["files"] + [(file_name, file_bytes)]
                    success, error_msg = send_email_oauth2(recipient, subject, body, attachments)
                    if success:
                        await message.answer("✅ Письмо с вложением отправлено.")
                    else:
                        await message.answer(f"{MESSAGES['email_failed']}\n❌ {error_msg}")
                    state["draft"] = {}
                    state["files"] = []
                    user_states[user_id]["email_router"] = state
                    return
                else:
                    await message.answer(MESSAGES["invalid_format"])
                    return
            else:
                state["files"].append((file_name, file_bytes))
                await message.answer(f"📎 Файл «{file_name}» прикреплён.")
        elif message.photo:
            # Берем фото с наивысшим качеством (последнее в массиве)
            photo = message.photo[-1]
            try:
                if message.bot:
                    file_stream = await message.bot.download(photo)  # type: ignore
                    if file_stream:
                        file_bytes = file_stream.read()  # type: ignore
                        file_stream.close()
                        file_name = f"screenshot_{photo.file_unique_id}.jpg"
                    else:
                        await message.answer("❌ Не удалось загрузить фото")
                        return
                else:
                    await message.answer("❌ Ошибка: отсутствует бот")
                    return
            except Exception as e:
                await message.answer(f"❌ Ошибка загрузки фото: {e}")
                return
            
            if message.caption:
                lines = message.caption.strip().splitlines()
                if len(lines) >= 2:
                    # Ждем 2 секунды для накопления файлов из групповых сообщений
                    await asyncio.sleep(2)
                    
                    subject = lines[0]
                    body = "\n".join(lines[1:])
                    recipient = state["recipient"] or default_recipient
                    attachments = state["files"] + [(file_name, file_bytes)]
                    success, error_msg = send_email_oauth2(recipient, subject, body, attachments)
                    if success:
                        await message.answer("✅ Письмо с изображением отправлено.")
                    else:
                        await message.answer(f"{MESSAGES['email_failed']}\n❌ {error_msg}")
                    state["draft"] = {}
                    state["files"] = []
                    user_states[user_id]["email_router"] = state
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
                success, error_msg = send_email_oauth2(recipient, subject, body, state["files"])
                if success:
                    if state["files"]:
                        await message.answer("✅ Письмо с вложением отправлено.")
                    else:
                        await message.answer("✅ Письмо отправлено.")
                else:
                    await message.answer(f"{MESSAGES['email_failed']}\n❌ {error_msg}")
                state["draft"] = {}
                state["files"] = []
            else:
                await message.answer(MESSAGES["invalid_format"])
        else:
            await message.answer("Вы уже отправили письмо или начали новое. Используйте Меню, чтобы выйти или сбросить.")

    else:
        await message.answer(f"Вы сказали: {text}")

    user_states[user_id]["email_router"] = state 