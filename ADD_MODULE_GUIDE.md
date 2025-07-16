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
- `1` - core (глобальные команды - ЗАРЕЗЕРВИРОВАНО)
- `10` - email_router (основной модуль)
- `15-20` - вспомогательные модули  
- `25-30` - пользовательские модули
- `30+` - специальные модули (id, debug и т.д.)

**⚠️ ВАЖНО**: Значение `1` зарезервировано для `core` модуля (глобальные команды `/start`, `/menu`)

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

## 6. 🚨 Важные архитектурные принципы

### ❌ Что НЕЛЬЗЯ делать в модулях:

#### **1. Глобальные команды в модулях**
```python
# ❌ ЗАПРЕЩЕНО - не добавляйте в свои модули:
@router.message(Command("start"))     # Только в core модуле!
@router.message(Command("menu"))      # Только в core модуле!
@router.message(Command("help"))      # Только в core модуле!
```

**Почему запрещено**: Если ваш модуль будет удален, эти команды перестанут работать для всего бота.

#### **2. Обработчики без фильтров**
```python
# ❌ ОПАСНО - перехватывает ВСЕ сообщения:
@router.message()
async def handle_all_messages(message: Message):

# ❌ ОПАСНО - перехватывает ВСЕ callback:
@router.callback_query()
async def handle_all_callbacks(callback: CallbackQuery):
```

**Последствия**: Ваш модуль может "украсть" сообщения, предназначенные другим модулям.

#### **3. Глобальные файлы для модуля**
```python
# ❌ НЕПРАВИЛЬНО - создавать глобальные файлы:
keyboards/my_module_ui.py      # Должно быть: routers/my_module/keyboards.py
services/my_module_service.py  # Должно быть: routers/my_module/services.py
```

### ✅ Правильная архитектура модуля:

#### **1. Модуль должен быть полностью автономным**
```
routers/my_module/
├── __init__.py         # Экспорт + MENU_CONFIG
├── router.py           # Логика модуля
├── messages.py         # Тексты модуля
├── keyboards.py        # Клавиатуры модуля (если нужны)
├── services.py         # Сервисы модуля (если нужны)
├── config.py           # Настройки модуля (если нужны)
├── .env                # Секреты модуля (если нужны)
└── auth/               # OAuth модуля (если нужна)
```

#### **2. Используйте правильные фильтры**
```python
# ✅ ПРАВИЛЬНО:
@router.callback_query(F.data == "my_specific_callback")
@router.message(F.text.contains("keyword"))
@router.message(Command("my_command"))  # Только команды вашего модуля!
```

#### **3. Принцип plug-and-play**
- Модуль можно скопировать в другой проект и он заработает
- Модуль не зависит от других модулей  
- Модуль можно удалить без поломки остального бота
- Все ресурсы (клавиатуры, сервисы) находятся внутри модуля

---

## 7. 🔄 Управление состояниями и навигация

### **⚠️ КРИТИЧЕСКИ ВАЖНО: Кнопка "Главное меню"**

**Проблема:** Многие модули неправильно обрабатывают кнопку "🏠 Главное меню", что приводит к багу - требуется **два нажатия** для возврата в меню.

#### **❌ НЕПРАВИЛЬНО - только очистка состояния:**
```python
@router.callback_query(F.data == "main_menu", StateFilter(MyStates.some_state))
async def exit_mode(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Возвращаюсь в меню!")  # ← Только поп-ап, НЕТ меню!
```

**Результат:** Пользователь видит поп-ап, но остается на том же экране. Нужно нажать еще раз.

#### **✅ ПРАВИЛЬНО - полная обработка:**

**Вариант 1: Полная обработка (рекомендуется)**
```python
@router.callback_query(F.data == "main_menu", StateFilter(MyStates.some_state))
async def exit_mode(callback: CallbackQuery, state: FSMContext):
    """Правильный выход в главное меню"""
    if not callback.message:
        return
    
    # 1. Очищаем состояние
    await state.clear()
    
    # 2. Импортируем главное меню
    from keyboards.main_menu import get_main_menu
    
    # 3. Отображаем главное меню
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())  # type: ignore
    await callback.answer("🏠 Возвращаемся в главное меню!")
```

**Вариант 2: Не перехватывать (для простых модулей)**
```python
# Просто НЕ добавляйте обработчик main_menu в свой модуль
# core модуль автоматически обработает его правильно
```

### **🏗️ Работа с состояниями FSM**

#### **1. Определение состояний модуля:**
```python
from aiogram.fsm.state import State, StatesGroup

class MyModuleStates(StatesGroup):
    waiting_for_input = State()
    processing_data = State()
    confirming_action = State()
```

#### **2. Правильная структура обработчиков:**
```python
my_router = Router()

# 1. Активация модуля (без состояния)
@my_router.callback_query(F.data == "my_mode")
async def activate_module(callback: CallbackQuery, state: FSMContext):
    # Устанавливаем состояние
    await state.set_state(MyModuleStates.waiting_for_input)
    await callback.message.edit_text("Модуль активирован!", reply_markup=get_back_menu())
    await callback.answer("✅ Готов к работе!")

# 2. Обработчики в состоянии (с фильтром состояния)
@my_router.message(StateFilter(MyModuleStates.waiting_for_input), F.text)
async def handle_input(message: Message, state: FSMContext):
    # Обрабатываем ввод пользователя
    await state.update_data(user_input=message.text)
    await state.set_state(MyModuleStates.processing_data)
    await message.reply("Обрабатываю данные...")

# 3. Правильный выход (ОБЯЗАТЕЛЬНО!)
@my_router.callback_query(F.data == "main_menu", StateFilter(MyModuleStates))
async def exit_module(callback: CallbackQuery, state: FSMContext):
    if not callback.message:
        return
    await state.clear()
    from keyboards.main_menu import get_main_menu
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())  # type: ignore
    await callback.answer("🏠 Возвращаемся в главное меню!")
```

#### **3. Клавиатура для возврата:**
```python
def get_back_menu():
    """Стандартная клавиатура для возврата в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
```

### **📋 Обязательные элементы модуля с состояниями:**

1. **Определение состояний** - `StatesGroup` класс
2. **Активация с установкой состояния** - `await state.set_state()`
3. **Обработчики с фильтрами состояния** - `StateFilter(MyStates.state_name)`
4. **Правильный выход** - очистка состояния + показ главного меню
5. **Клавиатура возврата** - кнопка "🏠 Главное меню" на каждом экране

### **⚡ Дополнительные рекомендации:**

#### **Обратная связь пользователю:**
```python
# ✅ Всегда отвечайте на callback нажатия
await callback.answer("✅ Действие выполнено!")  # Поп-ап
await callback.answer()  # Минимум - убрать "часики" загрузки
```

#### **Обработка ошибок состояния:**
```python
@my_router.message(StateFilter(MyModuleStates.waiting_for_input))
async def handle_wrong_input(message: Message):
    """Обработка неподходящих сообщений в состоянии"""
    await message.reply(
        "⚠️ Ожидается текстовое сообщение.\n\nПопробуйте еще раз:",
        reply_markup=get_back_menu()
    )
```

#### **Сохранение данных в состоянии:**
```python
# Сохранение данных
await state.update_data(username=message.text, file_id=message.document.file_id)

# Получение данных
data = await state.get_data()
username = data.get("username")
file_id = data.get("file_id")
```

---

## 8. 🔐 Модульная авторизация (для внешних API)

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

## 9. 🔧 Устранение проблем

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

## 10. 🔐 Управление секретами и переменными окружения

### 📂 Структура модуля с секретами:
```
routers/
  my_api_module/
    __init__.py
    router.py
    config.py           # Управление переменными модуля
    .env                # Секреты модуля (не попадет в git)
    .env.example        # Шаблон для других разработчиков
    messages.py
    auth/               # (опционально) для OAuth токенов
```

### 🌍 Принципы разделения настроек:

**Глобальные настройки (корневой `.env`):**
- `BOT_TOKEN` - токен Telegram бота
- `ALLOWED_USER_IDS` - разрешенные пользователи
- Общие настройки, используемые всем ботом

**Модульные настройки (локальный `.env`):**
- API ключи вашего сервиса
- Специфичные URL и конфигурации
- Токены OAuth для конкретного модуля

### 📝 Пример создания модуля с секретами:

#### 1. Создайте `.env.example` (шаблон):
```env
# Скопируйте в .env и заполните значения
MY_API_KEY=your_api_key_here
MY_SERVICE_URL=https://api.example.com
MY_WEBHOOK_SECRET=webhook_secret_here
```

#### 2. Создайте `config.py` модуля:
```python
"""
Конфигурация my_api_module
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла модуля
module_dir = Path(__file__).parent
env_path = module_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠️  Файл .env не найден в {module_dir}")
    print(f"📋 Скопируйте .env.example в .env и заполните значения")

# Переменные модуля
MY_API_KEY = os.getenv("MY_API_KEY")
MY_SERVICE_URL = os.getenv("MY_SERVICE_URL") 
MY_WEBHOOK_SECRET = os.getenv("MY_WEBHOOK_SECRET")

# Валидация обязательных переменных
REQUIRED_VARS = {
    "MY_API_KEY": MY_API_KEY,
    "MY_SERVICE_URL": MY_SERVICE_URL,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    raise ValueError(f"Отсутствуют переменные: {', '.join(missing_vars)}")

# Конфигурация модуля
MODULE_CONFIG = {
    'api_key': MY_API_KEY,
    'service_url': MY_SERVICE_URL,
    'webhook_secret': MY_WEBHOOK_SECRET,
    'timeout': 30,  # секунды
}
```

#### 3. Используйте в `router.py`:
```python
from .config import MODULE_CONFIG, MY_API_KEY
import httpx

@my_module_router.callback_query(F.data == "my_mode")
async def activate_module(callback: CallbackQuery):
    # Проверяем, что API ключ настроен
    if not MY_API_KEY:
        await callback.message.edit_text(
            "❌ Модуль не настроен!\n"
            "Создайте файл .env в папке модуля"
        )
        return
    
    # Используем API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            MODULE_CONFIG['service_url'],
            headers={'Authorization': f'Bearer {MY_API_KEY}'}
        )
```

### 🔧 Инструкции для пользователей:

В README модуля объясните:
```markdown
## Настройка секретов

1. Скопируйте `.env.example` в `.env`:
   ```bash
   cp routers/my_module/.env.example routers/my_module/.env
   ```

2. Заполните переменные в `.env`:
   ```env
   MY_API_KEY=ваш_настоящий_ключ
   MY_SERVICE_URL=https://real-api.com
   ```

3. Запустите бота - модуль автоматически загрузит настройки
```

### ⚠️ Важные моменты:

1. **Безопасность**: Файлы `.env` в модулях автоматически исключены из git
2. **Документация**: Всегда создавайте `.env.example` для других разработчиков
3. **Валидация**: Проверяйте обязательные переменные при запуске модуля
4. **Изоляция**: Модули не видят секреты друг друга
5. **Fallback**: Предусмотрите понятные сообщения об ошибках
6. **Модульность**: НЕ создавайте глобальные файлы для своего модуля (keyboards/my_module.py, services/my_module.py)
7. **Локальные ресурсы**: Клавиатуры, сервисы, конфиги должны быть внутри модуля

---

## 11. 📋 Чек-лист создания модуля

### Базовая структура:
- [ ] Создана папка `routers/my_module/`
- [ ] Создан `__init__.py` с экспортом роутера и `MENU_CONFIG`
- [ ] Создан `router.py` с объектом Router
- [ ] Создан `messages.py` с сообщениями
- [ ] Использован правильный синтаксис aiogram 3.x (`F.data == "callback"`)
- [ ] Callback_data уникален и совпадает в `MENU_CONFIG` и хендлере
- [ ] Добавлены фильтры для избежания конфликтов

### Состояния и навигация (если используются):
- [ ] Определен `StatesGroup` класс для состояний модуля
- [ ] Добавлен импорт `from aiogram.fsm.state import State, StatesGroup`
- [ ] Добавлен импорт `from aiogram.fsm.context import FSMContext`
- [ ] Добавлен импорт `from aiogram.filters import StateFilter`
- [ ] Активация модуля устанавливает состояние: `await state.set_state()`
- [ ] Обработчики используют фильтры состояния: `StateFilter(MyStates.state_name)`
- [ ] **КРИТИЧНО:** Правильно обрабатывается кнопка "Главное меню":
  - [ ] Добавлен обработчик `@router.callback_query(F.data == "main_menu", StateFilter(MyStates))`
  - [ ] Обработчик очищает состояние: `await state.clear()`
  - [ ] Обработчик импортирует меню: `from keyboards.main_menu import get_main_menu`
  - [ ] Обработчик отображает меню: `await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())`
  - [ ] Добавлен `# type: ignore` для типизации
- [ ] Создана функция `get_back_menu()` для клавиатуры возврата
- [ ] Все экраны модуля имеют кнопку "🏠 Главное меню"
- [ ] Добавлены обработчики неподходящих сообщений в состояниях
- [ ] Используется `await callback.answer()` для обратной связи

### Секреты и конфигурация (если нужны):
- [ ] Создан `.env.example` с шаблоном переменных
- [ ] Создан `config.py` с загрузкой модульных переменных
- [ ] Добавлена валидация обязательных переменных
- [ ] Проверена изоляция секретов модуля

### Авторизация (если нужна):
- [ ] (Опционально) Создана папка `auth/` для внешних API
- [ ] Создан `auth_manager.py` для управления токенами
- [ ] Создан `script.py` для первичной авторизации

### Тестирование и отладка:
- [ ] Модуль корректно загружается при запуске бота
- [ ] Кнопка модуля появляется в главном меню
- [ ] Нажатие на кнопку активирует правильную функцию
- [ ] Кнопка "🏠 Главное меню" работает с **первого нажатия**
- [ ] Протестированы все пути навигации в модуле
- [ ] Проверена обработка ошибок конфигурации и внешних API
- [ ] Убедиться, что модуль не перехватывает чужие сообщения
- [ ] Добавлены отладочные команды (опционально)
- [ ] Проверена работа с временными файлами и их очистка

---

## 12. 🧪 Тестирование и отладка модулей

### **🔍 Проверка базовой работы модуля:**

#### **1. Проверка загрузки модуля:**
```bash
# Запустите бота и проверьте логи
python bot.py

# Должны увидеть:
# ✅ Найден модуль: my_module
# ✅ Роутер зарегистрирован: my_module_router
```

#### **2. Проверка меню:**
```
/start → Ваш модуль должен быть в списке кнопок
Нажмите на кнопку → Должна активироваться правильная функция
```

#### **3. Проверка навигации:**
```
Нажмите "🏠 Главное меню" → Должны вернуться в главное меню за ОДНО нажатие
```

### **🐛 Частые проблемы и их решения:**

#### **Модуль не загружается:**
```python
# ❌ Частая ошибка:
from .router import my_module  # НЕ заканчивается на _router

# ✅ Правильно:
from .router import my_module_router
```

#### **Кнопка не работает:**
```python
# Проверьте совпадение callback_data:
MENU_CONFIG = {
    'callback_data': 'my_mode'  # ← Это должно совпадать
}

@router.callback_query(F.data == "my_mode")  # ← С этим
```

#### **Модуль "крадет" чужие сообщения:**
```python
# ❌ Опасно:
@router.message()  # Перехватывает ВСЕ сообщения

# ✅ Безопасно:
@router.message(StateFilter(MyStates.waiting_input), F.text)  # Только в состоянии
@router.message(F.text.contains("keyword"))  # Только с ключевым словом
```

#### **Двойное нажатие для возврата в меню:**
```python
# ❌ Неполная обработка:
@router.callback_query(F.data == "main_menu", StateFilter(MyStates))
async def exit_mode(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Выхожу...")  # ← НЕТ отображения меню!

# ✅ Полная обработка:
@router.callback_query(F.data == "main_menu", StateFilter(MyStates))
async def exit_mode(callback: CallbackQuery, state: FSMContext):
    if not callback.message:
        return
    await state.clear()
    from keyboards.main_menu import get_main_menu
    await callback.message.edit_text("📋 Главное меню:", reply_markup=get_main_menu())  # type: ignore
    await callback.answer("🏠 Возвращаемся в главное меню!")
```

### **📊 Отладочные техники:**

#### **1. Логирование состояний:**
```python
import logging
logger = logging.getLogger(__name__)

@router.message(StateFilter(MyStates.waiting_input))
async def handle_input(message: Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"Получено сообщение в состоянии: {current_state}")
    logger.info(f"Текст сообщения: {message.text}")
```

#### **2. Проверка данных состояния:**
```python
@router.callback_query(F.data == "debug_state")
async def debug_state(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    state_data = await state.get_data()
    
    debug_info = f"""
🐛 **Отладочная информация:**
Состояние: {current_state}
Данные: {state_data}
"""
    await callback.message.edit_text(debug_info)
```

#### **3. Проверка конфигурации:**
```python
# Добавьте команду для проверки настроек модуля
@router.message(Command("debug_config"))
async def debug_config(message: Message):
    config_info = f"""
🔧 **Конфигурация модуля:**
API ключ: {"✅ Настроен" if MY_API_KEY else "❌ Отсутствует"}
Timeout: {MODULE_CONFIG.get('timeout', 'N/A')}
"""
    await message.reply(config_info)
```

### **⚡ Советы по производительности:**

1. **Используйте async/await правильно** - не блокируйте основной поток
2. **Ограничивайте размер файлов** - проверяйте лимиты до обработки
3. **Обрабатывайте ошибки** - всегда предусмотрите try/except для внешних API
4. **Очищайте ресурсы** - удаляйте временные файлы
5. **Кэшируйте данные** - не делайте повторные запросы к API

### **🔐 Безопасность:**

1. **Никогда не логируйте API ключи** - используйте `[СКРЫТО]` в логах
2. **Проверяйте разрешения** - используйте `ALLOWED_USER_IDS`
3. **Валидируйте ввод** - проверяйте файлы и текст от пользователей
4. **Ограничивайте ресурсы** - размер файлов, частота запросов

---

## 13. 💡 Примеры готовых модулей

### Системный модуль: `core` 
- **НЕ ТРОГАЙТЕ ЕГО!** - обрабатывает глобальные команды `/start`, `/menu`
- Показывает главное меню всех модулей
- Всегда должен быть первым в списке (order: 1)
- Пример правильной архитектуры для глобальных команд

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
- Пример полностью автономного модуля с собственными клавиатурами и сервисами

Изучите эти модули для понимания лучших практик! 📚 