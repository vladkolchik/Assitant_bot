# 📦 Инструкция: Как добавить свой модуль (plug-and-play)

## 1. Создайте структуру модуля

В папке `routers/` создайте подпапку с уникальным именем вашего модуля, например, `my_module`:

```
routers/
  my_module/
    __init__.py
    router.py
    messages.py
    (config.py)         # если нужны свои настройки
    (keyboards.py)      # если нужны свои клавиатуры
    (services/)         # если есть бизнес-логика
    (auth/)            # если модулю нужна авторизация
```

---

## 2. Реализуйте роутер

В `router.py`:
- Создайте объект `Router` из aiogram.
- Опишите хендлеры (обработчики команд, сообщений, callback и т.д.).
- Импортируйте свои сообщения из `messages.py`.
- Если нужны глобальные сообщения (`start`, `no_access`), импортируйте их из корневого `messages.py`:
  ```python
  from .messages import MESSAGES  # локальные
  from messages import MESSAGES as GLOBAL_MESSAGES  # глобальные
  ```

**⚠️ Важно для callback_query в aiogram 3.x:**
```python
from aiogram import F

# Правильно:
@my_module_router.callback_query(F.data == "my_callback")

# Неправильно:
@my_module_router.callback_query(text="my_callback")  # Старый синтаксис 2.x
```

---

## 3. Экспортируйте роутер и настройте меню

В `__init__.py` модуля:
```python
from .router import my_module_router

# Конфигурация для главного меню (ОБЯЗАТЕЛЬНО!)
MENU_CONFIG = {
    'text': '🔧 Мой модуль',
    'callback_data': 'my_mode',
    'order': 30  # порядок в меню (10-email, 15-test, 20-id)
}
```

**🔢 Рекомендуемые значения order:**
- `10` - email_router (основной)
- `15` - вспомогательные модули  
- `20` - id_module
- `25+` - пользовательские модули

---

## 4. Создайте сообщения модуля

В `messages.py`:
```python
MESSAGES = {
    "activation": "🔧 Мой модуль активирован!",
    "help": "Это справка по моему модулю",
    "error": "Ошибка в моем модуле"
}
```

---

## 5. Пример простого модуля

### `router.py`:
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from .messages import MESSAGES

my_module_router = Router()

@my_module_router.callback_query(F.data == "my_mode")
async def activate_my_module(callback: CallbackQuery):
    await callback.message.edit_text(MESSAGES["activation"])
    await callback.answer("Модуль активирован!")

@my_module_router.message(F.text.contains("привет"))
async def hello_handler(message: Message):
    await message.reply("Привет из моего модуля!")
```

### `messages.py`:
```python
MESSAGES = {
    "activation": "🔧 Мой модуль активирован!\n\nНапишите 'привет' для тестирования.",
}
```

### `__init__.py`:
```python
from .router import my_module_router

MENU_CONFIG = {
    'text': '🔧 Мой модуль',
    'callback_data': 'my_mode',
    'order': 30
}
```

---

## 6. 🔐 Модульная авторизация (для внешних API)

Если ваш модуль работает с внешними сервисами (Google API, Discord API и т.д.), создайте папку `auth/`:

### Структура модуля с авторизацией:
```
routers/
  my_api_module/
    __init__.py
    router.py
    messages.py
    auth/                    # Авторизация модуля
      __init__.py
      auth_manager.py        # Менеджер авторизации
      script.py             # Скрипт получения токенов
      client_secret.json    # Конфиги API
      token.pkl            # Токены (создается автоматически)
```

### Пример auth_manager.py:
```python
"""
Менеджер авторизации для вашего API
"""
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MyAPIAuthManager:
    def __init__(self, auth_dir: str | None = None):
        if auth_dir:
            self.auth_dir = Path(auth_dir)
        else:
            self.auth_dir = Path(__file__).parent
        
        self.token_file = self.auth_dir / "token.pkl"
        self.config_file = self.auth_dir / "client_secret.json"
        self.auth_dir.mkdir(exist_ok=True)
    
    def load_credentials(self):
        """Загружает токены из файла"""
        try:
            with open(self.token_file, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            logger.error(f"Токен не найден: {self.token_file}")
            return None
    
    def save_credentials(self, creds):
        """Сохраняет токены в файл"""
        with open(self.token_file, "wb") as f:
            pickle.dump(creds, f)
        logger.info(f"Токен сохранен: {self.token_file}")
    
    def is_authorized(self):
        """Проверяет авторизацию"""
        creds = self.load_credentials()
        return creds is not None
```

### Пример script.py для авторизации:
```python
"""
Скрипт авторизации для вашего API
"""
from pathlib import Path
import pickle

def main():
    auth_dir = Path(__file__).parent
    print(f"🔐 Начинаем авторизацию...")
    
    # Здесь ваша логика получения токенов
    # Например, OAuth flow, API ключи и т.д.
    
    token = "your_api_token_here"
    
    with open(auth_dir / "token.pkl", "wb") as f:
        pickle.dump(token, f)
    
    print(f"✅ Авторизация завершена!")

if __name__ == "__main__":
    main()
```

### Использование в модуле:
```python
# В router.py
from .auth import MyAPIAuthManager

auth_manager = MyAPIAuthManager()

@my_module_router.callback_query(F.data == "my_mode")
async def activate_module(callback: CallbackQuery):
    if not auth_manager.is_authorized():
        await callback.message.edit_text(
            "❌ Требуется авторизация!\n"
            f"Выполните: python {auth_manager.auth_dir}/script.py"
        )
        return
    
    # Основная логика модуля
    await callback.message.edit_text("✅ Модуль работает!")
```

---

## 7. 🔧 Устранение проблем

### Кнопка не работает
1. **Проверьте callback_data** в `MENU_CONFIG` и хендлере:
   ```python
   # В __init__.py
   'callback_data': 'my_mode'
   
   # В router.py  
   @router.callback_query(F.data == "my_mode")  # Должно совпадать!
   ```

2. **Убедитесь в правильном синтаксисе aiogram 3.x:**
   ```python
   # ✅ Правильно
   @router.callback_query(F.data == "my_mode")
   
   # ❌ Неправильно (aiogram 2.x)
   @router.callback_query(text="my_mode")
   ```

### Модуль не загружается
1. **Проверьте, что в `__init__.py` есть экспорт роутера:**
   ```python
   from .router import my_module_router  # Обязательно!
   ```

2. **Проверьте имя роутера** - должно заканчиваться на `_router`:
   ```python
   my_module_router = Router()  # ✅ Правильно
   my_module = Router()         # ❌ Не загрузится
   ```

### Конфликты между модулями
1. **Используйте фильтры** для избежания перехвата чужих callback:
   ```python
   # ✅ Правильно - только свои callback
   @router.callback_query(F.data == "my_mode")
   
   # ❌ Неправильно - перехватывает ВСЕ callback
   @router.callback_query()
   ```

2. **Проверьте уникальность callback_data** между модулями

### Проблемы с авторизацией
1. **Проверьте пути к файлам** в auth_manager
2. **Убедитесь, что скрипт авторизации создает токены в правильной папке**
3. **Проверьте права доступа** к папке auth/

---

## 8. 📋 Чек-лист создания модуля

- [ ] Создана папка `routers/my_module/`
- [ ] Создан `__init__.py` с экспортом роутера и `MENU_CONFIG`
- [ ] Создан `router.py` с объектом Router
- [ ] Создан `messages.py` с сообщениями
- [ ] Использован правильный синтаксис aiogram 3.x (`F.data == "callback"`)
- [ ] Callback_data уникален и совпадает в `MENU_CONFIG` и хендлере
- [ ] Добавлены фильтры для избежания конфликтов
- [ ] (Опционально) Создана папка `auth/` для внешних API
- [ ] Протестирована работа кнопки и хендлеров

---

## 9. 💡 Примеры готовых модулей

### Простой модуль: `id_module`
- Показывает ID пользователя и чата
- Один callback хендлер
- Минимальная структура

### Демонстрационный: `test_module` 
- Показывает разные типы фильтров
- Callback, текстовые и эмодзи хендлеры
- `callback.answer()` для обратной связи

### Сложный модуль: `email_router`
- Множественные состояния пользователя
- Авторизация через Google OAuth
- Работа с файлами и вложениями
- Собственная папка `auth/` с менеджером авторизации

Изучите эти модули для понимания лучших практик! 📚 