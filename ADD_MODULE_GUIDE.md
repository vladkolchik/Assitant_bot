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

---

## 3. Экспортируйте роутер

В `__init__.py` модуля:
```python
from .router import my_module_router  # или как назван объект Router
```
(Главное — экспортировать объект Router, чтобы автозагрузка его увидела.)

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
- Модуль подхватится автоматически благодаря автозагрузке роутеров.

---

## 7. Проверьте работу

- Запустите бота.
- Новый модуль будет автоматически подключён, если экспортирует объект Router.

---

## 8. Пример минимального модуля

**routers/hello_module/router.py**
```python
from aiogram import Router
from aiogram.types import Message
from .messages import MESSAGES

hello_module_router = Router()

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

**routers/hello_module/__init__.py**
```python
from .router import hello_module_router
```

---

## 9. Рекомендации

- Давайте объекту Router уникальное имя (например, `my_module_router`), чтобы избежать конфликтов.
- Все импорты внутри модуля делайте относительными (`from .messages import MESSAGES`).
- Не используйте глобальные переменные, если это не требуется.
- Для сложных модулей используйте свою папку `services/` и/или `config.py`.

---

## 10. Если что-то не работает

- Проверьте, что в папке модуля есть `__init__.py` и он экспортирует объект Router.
- Проверьте, что нет конфликтов имён с другими модулями.
- Посмотрите примеры в других модулях или обратитесь к документации aiogram.

---

**Теперь вы можете легко расширять функционал бота, просто добавляя новые модули в папку `routers/`!** 