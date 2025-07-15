"""
Клавиатуры email модуля - модульный подход
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_email_menu():
    """Основное меню email модуля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Прикреплённые файлы", callback_data="show_attachments")],
        [InlineKeyboardButton(text="🔧 Кому направлять письма", callback_data="recipient_menu")],
        [InlineKeyboardButton(text="🗑 Сбросить черновик", callback_data="reset_draft")],
        [InlineKeyboardButton(text="📭 Выйти из email режима", callback_data="exit_email_mode")]
    ])

def get_recipient_menu():
    """Меню управления получателем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_recipient")],
        [InlineKeyboardButton(text="♻️ Сбросить", callback_data="reset_recipient")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_email_menu")]
    ]) 