from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import importlib
import pkgutil
from pathlib import Path
from typing import List, Dict, Any

class MenuButton:
    """Класс для представления кнопки главного меню"""
    def __init__(self, text: str, callback_data: str, order: int = 999):
        self.text = text
        self.callback_data = callback_data
        self.order = order

def discover_menu_buttons() -> List[MenuButton]:
    """Автоматически находит кнопки из конфигураций модулей"""
    buttons = []
    routers_path = Path("routers")
    
    # Проходим по всем модулям в папке routers
    for _, module_name, _ in pkgutil.iter_modules([str(routers_path)]):
        if module_name.startswith("_"):
            continue
            
        try:
            # Пытаемся импортировать модуль и найти MENU_CONFIG
            module = importlib.import_module(f"routers.{module_name}")
            
            if hasattr(module, 'MENU_CONFIG'):
                config = module.MENU_CONFIG
                buttons.append(MenuButton(
                    text=config['text'],
                    callback_data=config['callback_data'], 
                    order=config.get('order', 999)
                ))
        except ImportError:
            # Модуль не найден или не может быть импортирован
            continue
        except Exception as e:
            # Ошибка в конфигурации модуля - пропускаем
            print(f"Warning: Error loading menu config from {module_name}: {e}")
            continue
    
    # Сортируем кнопки по порядку
    return sorted(buttons, key=lambda x: x.order)

def get_main_menu() -> InlineKeyboardMarkup:
    """Генерирует главное меню из всех зарегистрированных модулей"""
    buttons = discover_menu_buttons()
    
    # Создаем клавиатуру с кнопками
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn.text, callback_data=btn.callback_data)]
        for btn in buttons
    ]) 