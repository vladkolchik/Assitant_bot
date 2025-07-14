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

# Конфигурация для главного меню (опционально)
MENU_CONFIG = {
    'text': '🔧 Мой модуль',           # Текст кнопки
    'callback_data': 'my_mode',        # Callback данные
    'order': 30                        # Порядок в меню (меньше = выше)
}
```

**Как работает автоматическое меню:**
- Если добавите `MENU_CONFIG` - кнопка автоматически появится в главном меню
- Если не добавите - модуль будет работать, но без кнопки в меню
- `order` определяет позицию: 10, 20, 30... (меньше число = выше в меню)

---

## 4. Добавьте сообщения

В `messages.py` модуля:
- Описывайте только специфичные для этого модуля сообщения.
- Не дублируйте глобальные (`start`, `no_access`).

---

## 5. (Опционально) Добавьте сервисы, клавиатуры, конфиг

- Если модулю нужны свои сервисы — создайте папку `services/` внутри модуля.
- Если нужны клавиатуры — файл `keyboards.py`.
- Если нужны настройки — файл `config.py` (и брать переменные только из него).

---

## 6. Не трогайте другие файлы проекта

- Не нужно ничего менять в `bot.py`, `routers/__init__.py`, общем `messages.py` и т.д.
- НЕ НУЖНО модифицировать `keyboards/email_ui.py` или другие файлы модулей
- Модуль подхватится автоматически благодаря автозагрузке роутеров.
- Кнопка в главном меню появится автоматически, если есть `MENU_CONFIG`.

---

## 7. Проверьте работу

- Запустите бота.
- Новый модуль будет автоматически подключён, если экспортирует объект Router.
- Кнопка появится в главном меню, если добавили `MENU_CONFIG`.

---

## 8. Пример минимального модуля

**routers/hello_module/__init__.py**
```python
from .router import hello_module_router

# Кнопка в главном меню
MENU_CONFIG = {
    'text': '👋 Привет',
    'callback_data': 'hello_mode',
    'order': 50
}
```

**routers/hello_module/router.py**
```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from .messages import MESSAGES

hello_module_router = Router()

# Обработка callback кнопки из главного меню
@hello_module_router.callback_query(F.data == "hello_mode")
async def hello_callback(callback: CallbackQuery):
    await callback.message.answer(MESSAGES["hello"])
    await callback.answer()

# Обработка текстовых сообщений (опционально)
@hello_module_router.message()
async def hello_handler(message: Message):
    await message.answer(MESSAGES["hello"])
```

**routers/hello_module/messages.py**
```python
MESSAGES = {
    "hello": "Привет! Это новый модуль 👋"
}
```

---

## 9. Рекомендации

- Давайте объекту Router уникальное имя (например, `my_module_router`), чтобы избежать конфликтов.
- Все импорты внутри модуля делайте относительными (`from .messages import MESSAGES`).
- Используйте специфичные фильтры для callback_query: `F.data == "specific_value"`.
- Не используйте общие обработчики `@router.callback_query()` без фильтров - они перехватывают все события.
- Для сложных модулей используйте свою папку `services/` и/или `config.py`.
- Выбирайте `order` кратным 10 (10, 20, 30...) для удобства вставки новых модулей.

---

## 10. Если что-то не работает

### Модуль не подключается:
- Проверьте, что в папке модуля есть `__init__.py` и он экспортирует объект Router.
- Убедитесь, что имя объекта Router уникально.

### Кнопка не появляется в меню:
- Проверьте, что `MENU_CONFIG` добавлен в `__init__.py` модуля.
- Проверьте синтаксис конфигурации (нужны 'text', 'callback_data').
- Перезапустите бота.

### Callback не обрабатывается:
- Убедитесь, что используете правильный синтаксис: `F.data == "callback_name"`.
- Проверьте, что `callback_data` в `MENU_CONFIG` совпадает с фильтром в обработчике.
- Убедитесь, что импортировали `from aiogram import F`.

### Конфликты с другими модулями:
- Не используйте общие обработчики `@router.callback_query()` без фильтров.
- Используйте уникальные названия для callback_data.
- Посмотрите примеры в других модулях или обратитесь к документации aiogram.

---

**Теперь вы можете легко расширять функционал бота, просто добавляя новые модули в папку `routers/`! Система автоматически подхватит ваш модуль и добавит кнопку в главное меню.** 