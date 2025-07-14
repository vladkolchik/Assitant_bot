from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Отправка email", callback_data="email_mode")],
        [InlineKeyboardButton(text="🆔 Получить ID", callback_data="id_mode")]
    ])

def get_email_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Прикреплённые файлы", callback_data="show_attachments")],
        [InlineKeyboardButton(text="🔧 Кому направлять письма", callback_data="recipient_menu")],
        [InlineKeyboardButton(text="🗑 Сбросить черновик", callback_data="reset_draft")],
        [InlineKeyboardButton(text="📭 Выйти из email режима", callback_data="exit_email_mode")]
    ])

def get_recipient_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_recipient")],
        [InlineKeyboardButton(text="♻️ Сбросить", callback_data="reset_recipient")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_email_menu")]
    ])
