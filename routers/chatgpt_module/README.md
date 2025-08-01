# 🤖 ChatGPT + Whisper модуль

**Версия:** 2.1.0  
**Дата обновления:** Январь 2025  
**Совместимость:** OpenAI API v1.95.1+, Whisper API, Mem0 API

Модуль интеграции с OpenAI ChatGPT API и Whisper для Telegram бота с поддержкой аудио.

## 🌟 Возможности

- 💬 Общение с ChatGPT текстом и голосом
- 🧠 **Долговременная память** через Mem0 (NEW!)
- 🎤 Распознавание речи через OpenAI Whisper
- 🔄 Поддержка локального и облачного Whisper
- 🎵 Обработка аудио, голосовых и кружочков
- 🌍 Поддержка множества языков
- 🎛️ Настраиваемые параметры (модель, температура, токены)
- 🔐 Модульное управление секретами
- 🏠 Интеграция с главным меню бота
- ⚡ Асинхронная обработка запросов
- 🎯 **Contextual память:** бот помнит ваши предпочтения и историю
- 🗑️ **Управление памятью:** очистка воспоминаний по требованию

## 📋 Требования

### Обязательно:
1. **OpenAI API ключ** - получите на [platform.openai.com](https://platform.openai.com/api-keys)
2. **Средства на балансе OpenAI** - для работы ChatGPT и Whisper API
3. **Python библиотеки** - устанавливаются автоматически

### Для долговременной памяти (опционально):
4. **Mem0 API ключ** - получите на [app.mem0.ai](https://app.mem0.ai) (бесплатный тариф доступен)

### Для локального Whisper (опционально):
5. **FFmpeg** - для конвертации аудио
6. **PyTorch** - для работы локальной модели Whisper

## ⚙️ Настройка

### 1. Скопируйте шаблон переменных
```bash
cp routers/chatgpt_module/env.example routers/chatgpt_module/.env
```

### 2. Настройте переменные в `.env`
```env
# ===== CHATGPT НАСТРОЙКИ =====
OPENAI_API_KEY=sk-ваш_настоящий_ключ
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# ===== MEM0 ПАМЯТЬ НАСТРОЙКИ =====
# Долговременная память диалогов (необязательно)
MEM0_API_KEY=your-mem0-api-key
MEM0_ENABLED=true

# ===== WHISPER НАСТРОЙКИ =====
# Выберите режим: "api" или "local"
WHISPER_MODE=api
WHISPER_MODEL=whisper-1
LOCAL_WHISPER_MODEL=base
WHISPER_LANGUAGE=ru

# ===== АУДИО НАСТРОЙКИ =====
MAX_AUDIO_SIZE_MB=25
MAX_AUDIO_DURATION_SEC=300
AUDIO_TEMP_DIR=temp_audio
AUTO_CLEANUP_TEMP_FILES=true
```

### 3. Получите API ключ OpenAI

1. Зайдите на [platform.openai.com](https://platform.openai.com)
2. Создайте аккаунт или войдите
3. Перейдите в раздел [API Keys](https://platform.openai.com/api-keys)
4. Нажмите "Create new secret key"
5. Скопируйте ключ в файл `.env`

### 4. Выберите режим Whisper

#### Вариант A: Whisper API (рекомендуется)
```env
WHISPER_MODE=api
```
**Преимущества:** Быстро, точно, не требует мощного железа  
**Недостатки:** Платно (~$0.006 за минуту)

#### Вариант B: Локальный Whisper
```env
WHISPER_MODE=local
LOCAL_WHISPER_MODEL=base  # tiny, base, small, medium, large-v3
```
**Преимущества:** Бесплатно, приватно  
**Недостатки:** Медленно, требует мощного процессора/GPU

### 5. Установите дополнительные зависимости

#### Для базовой функциональности:
```bash
pip install openai aiofiles aiohttp
```

#### Для долговременной памяти:
```bash
pip install mem0ai
```

#### Для локального Whisper:
```bash
pip install openai-whisper ffmpeg-python
```

#### Установка FFmpeg:
**Windows:**
```bash
# Через chocolatey
choco install ffmpeg

# Или скачать с https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 6. Настройте Mem0 память (опционально)

#### Для включения долговременной памяти:

1. **Регистрация в Mem0:**
   - Перейдите на [app.mem0.ai](https://app.mem0.ai)
   - Создайте бесплатный аккаунт
   - Получите API ключ из дашборда

2. **Конфигурация:**
   ```env
   MEM0_API_KEY=ваш-mem0-api-ключ
   MEM0_ENABLED=true
   ```

3. **Установите библиотеку:**
   ```bash
   pip install mem0ai
   ```

4. **Возможности памяти:**
   - ✅ **10,000 воспоминаний** на бесплатном тарифе
   - ✅ **1,000 поисков** в месяц бесплатно  
   - ✅ Бот помнит ваше имя, предпочтения, историю
   - ✅ Кнопка "Очистить память" для сброса
   - ✅ Контекстные ответы на основе прошлых диалогов

**Без Mem0:** Бот работает без памяти (каждый диалог независим)  
**С Mem0:** Бот помнит контекст между сессиями 🧠

### 7. Добавьте средства на баланс OpenAI

1. Перейдите в [Billing](https://platform.openai.com/account/billing)
2. Добавьте способ оплаты
3. Пополните баланс (минимум $5)

### 8. Запустите бота
```bash
python bot.py
```

## 🎯 Использование

### Активация модуля:
1. Запустите бота командой `/start`
2. Нажмите кнопку "🤖 ChatGPT" в главном меню
3. Модуль готов к работе!

### Поддерживаемые форматы:

#### 📝 Текстовые сообщения
- Прямое общение с ChatGPT
- Примеры: "Расскажи анекдот", "Переведи на английский"

#### 🎤 Голосовые сообщения  
- Нажмите и удерживайте кнопку записи в Telegram
- Говорите четко на русском или другом языке
- AI распознает речь и ответит

#### ⭕ Кружочки (видео заметки)
- Нажмите на кнопку камеры и записывайте кружочек
- Аудио извлекается и обрабатывается через Whisper
- Поддерживается извлечение звука из видео

#### 🎵 Аудио файлы
- Загрузите MP3, WAV, OGG, M4A файлы
- Максимум 25 МБ и 5 минут по умолчанию
- Полная обработка с высоким качеством

### Примеры использования:

**Текст:**
```
Пользователь: Объясни квантовую физику простыми словами
ChatGPT: Квантовая физика изучает поведение очень маленьких частиц...
```

**Голосовое:**
```
🎤 Пользователь: [голосовое] "Переведи 'Hello world' на русский"
✅ Речь распознана! (OpenAI Whisper API)
📝 Текст: Переведи Hello world на русский
🤖 ChatGPT: "Hello world" переводится как "Привет, мир!"
```

**Кружочек:**
```
⭕ Пользователь: [кружочек с вопросом]
🎧 Обрабатываю аудио... Распознаю речь с помощью Whisper
✅ Речь распознана! (Локальный Whisper)
🎤 Голосовое → 🤖 ChatGPT: [ответ]
```

**Долговременная память (с Mem0):**
```
День 1:
Пользователь: Привет, меня зовут Влад, я разработчик
ChatGPT: Привет, Влад! Приятно познакомиться. Чем занимаешься в разработке?

День 2:
Пользователь: Как дела?
ChatGPT: Привет, Влад! У меня всё хорошо. Как продвигается разработка?

🧠 Загружен контекст из памяти: 1 воспоминаний
```

**Управление памятью:**
```
Кнопка "Очистить память" → Память очищена для пользователя
Команда /chatgpt_info → Показывает статус памяти: Активно
```

## 🔧 Конфигурация

### Модели ChatGPT
- `gpt-3.5-turbo` - быстрый и дешевый (рекомендуется)
- `gpt-4` - более умный, но дорогой  
- `gpt-4-turbo-preview` - новейшая версия GPT-4

### Модели Whisper

#### API модели:
- `whisper-1` - единственная доступная модель API

#### Локальные модели:
- `tiny` - самая быстрая, низкая точность
- `base` - хороший баланс скорости и точности ⭐
- `small` - лучше точность, медленнее
- `medium` - очень хорошая точность
- `large-v3` - максимальная точность, очень медленно

### Языки Whisper
Поддерживаются 99+ языков: `ru`, `en`, `de`, `fr`, `es`, `it`, `ja`, `ko`, `zh`, `ar`, `hi` и др.

### Параметры аудио
```env
MAX_AUDIO_SIZE_MB=25          # Максимальный размер файла
MAX_AUDIO_DURATION_SEC=300    # Максимальная длительность (5 минут)
AUDIO_TEMP_DIR=temp_audio     # Папка для временных файлов
AUTO_CLEANUP_TEMP_FILES=true  # Автоочистка
```

## 🚨 Устранение проблем

### "Модуль не настроен"
- ✅ Проверьте наличие файла `.env` в папке модуля
- ✅ Убедитесь что `OPENAI_API_KEY` заполнен
- ✅ Перезапустите бота

### "Ошибка OpenAI API"
- ✅ Проверьте корректность API ключа
- ✅ Убедитесь что на балансе есть средства
- ✅ Проверьте доступность сервисов OpenAI
- ✅ Проверьте лимиты API

### "Ошибка обработки аудио"
**Для API режима:**
- ✅ Проверьте баланс OpenAI (Whisper API платный)
- ✅ Убедитесь что файл не превышает лимиты

**For локального режима:**
- ✅ Установите зависимости: `pip install openai-whisper ffmpeg-python`
- ✅ Установите FFmpeg в системе
- ✅ Проверьте свободное место на диске
- ✅ Дождитесь загрузки модели (при первом запуске)

### "Речь не обнаружена"
- 🎤 Говорите четче и громче
- 🔇 Запишите в тихом месте без шума
- ⏸️ Сделайте паузу перед началом речи
- 🌍 Убедитесь что язык указан корректно

### "Память не работает"
- ✅ Проверьте наличие `MEM0_API_KEY` в `.env` файле
- ✅ Убедитесь что `MEM0_ENABLED=true`
- ✅ Установите библиотеку: `pip install mem0ai`
- ✅ Проверьте API ключ на [app.mem0.ai](https://app.mem0.ai)
- ✅ Убедитесь что не превышены лимиты бесплатного тарифа

### "Контекст не загружается"
- ✅ Включите отладку (раскомментируйте debug строки в коде)
- ✅ Проверьте логи на наличие ошибок Mem0
- ✅ Попробуйте очистить память и начать заново

### Библиотеки не установлены
```bash
# Базовые зависимости
pip install openai aiofiles aiohttp

# Для памяти
pip install mem0ai

# Для локального Whisper
pip install openai-whisper ffmpeg-python

# Для ускорения на GPU (опционально)
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
```

## 💰 Стоимость

### OpenAI API (на январь 2025):

**ChatGPT:**
- `gpt-3.5-turbo`: ~$0.002 за 1K токенов
- `gpt-4`: ~$0.03 за 1K токенов  
- `gpt-4-turbo`: ~$0.01 за 1K токенов

**Whisper API:**
- $0.006 за минуту аудио
- Примерно $0.36 за час

### Mem0 Memory API (на январь 2025):

**Бесплатный тариф:**
- ✅ **10,000 воспоминаний** в месяц
- ✅ **1,000 поисков** в месяц
- ✅ Достаточно для личного использования

**Платные тарифы:**
- **Starter** ($19/мес): 50,000 воспоминаний, 5,000 поисков
- **Pro** ($249/мес): Безлимит воспоминаний, 50,000 поисков

**Пример расчета для личного использования:** 
- 50 сообщений в день × 30 дней = 1,500 сообщений в месяц
- Бесплатного тарифа хватает на **годы использования**! 🎉

### Локальный Whisper:
- Полностью бесплатно
- Требует мощного процессора/GPU
- Время обработки: 1-10x от длительности аудио

**Комбинированный пример:**
- 10 голосовых + текстовых сообщений = ~$0.032 (OpenAI) + $0 (Mem0) = **$0.032 за сессию**

## 🔐 Безопасность

### Рекомендации:
- ❌ Не публикуйте API ключ в коде
- ✅ Используйте `.env` файл (исключен из git)
- 🔄 Регулярно обновляйте API ключи
- 📊 Мониторьте расходы в OpenAI Dashboard
- 🗑️ Включайте автоочистку временных файлов

### Приватность:
- **API режим:** Аудио отправляется на серверы OpenAI
- **Локальный режим:** Аудио обрабатывается локально
- **Mem0 память:** Диалоги сохраняются на серверах Mem0 (изолированно по пользователям)
- **Без памяти:** Полная приватность, ничего не сохраняется

## 🏗️ Архитектура модуля

```
routers/chatgpt_module/
├── __init__.py         # Экспорт + MENU_CONFIG
├── router.py           # Логика обработки ChatGPT + аудио
├── config.py           # Управление переменными .env
├── services.py         # Сервисы для работы с аудио и Whisper
├── memory_service.py   # Сервис долговременной памяти Mem0
├── messages.py         # Тексты модуля
├── temp_audio/         # Временные аудио файлы (создается автоматически)
├── .env                # Секреты (создайте сами)
├── env.example         # Шаблон переменных
└── README.md           # Эта документация
```

## 📈 Производительность

### Benchmarks (примерные значения):

**Whisper API:**
- Время обработки: 2-5 секунд на минуту аудио
- Точность: 95-98% для качественной записи
- Поддержка языков: 99+

**Локальный Whisper:**
- `tiny` модель: 0.1x-0.5x реального времени
- `base` модель: 0.5x-1x реального времени  
- `large-v3` модель: 2x-5x реального времени
- Точность: 90-97% в зависимости от модели

## 📝 История версий

### v2.1.0 (Январь 2025) - MEMORY UPDATE 🧠
- ✅ **Долговременная память:** Интеграция с Mem0 API
- ✅ **Контекстные диалоги:** Бот помнит пользователей между сессиями
- ✅ **Умная память:** Автоматическое сохранение и поиск релевантных воспоминаний
- ✅ **Управление памятью:** Кнопка очистки, статистика, профили пользователей
- ✅ **Reasoning-модели:** Исправлена передача контекста для o1/o3/o4 серий
- ✅ **Бесплатная память:** 10,000 воспоминаний на Mem0 Free tier
- ✅ **Новая зависимость:** mem0ai библиотека

### v2.0.0 (Январь 2025) - MAJOR UPDATE 🎉
- ✅ **Поддержка аудио:** голосовые, кружочки, аудио файлы
- ✅ **Интеграция Whisper:** API и локальный режимы
- ✅ **Умная обработка:** автоопределение языка, fallback режимы
- ✅ **Расширенная конфигурация:** лимиты размера, длительности
- ✅ **Улучшенные сообщения:** детальная обратная связь
- ✅ **Автоочистка:** управление временными файлами
- ✅ **Новые зависимости:** aiofiles, aiohttp, опционально whisper

### v1.1.0 (Январь 2025)
- ✅ Обновление до OpenAI API v1.95.1
- ✅ Исправление ошибок совместимости
- ✅ Улучшенная обработка ошибок API
- ✅ Обновленная документация

### v1.0.0 (Январь 2025)
- 🎉 Первоначальный релиз
- 💬 Базовое общение с ChatGPT
- 🔐 Модульное управление секретами
- 🏠 Интеграция с главным меню

---

**Модуль полностью автономен** - можно скопировать в другой проект и он заработает! 🚀

## 🎓 Дополнительные ресурсы

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Whisper GitHub](https://github.com/openai/whisper)
- [Mem0 Platform](https://app.mem0.ai) - Регистрация и API ключи
- [Mem0 Documentation](https://docs.mem0.ai) - Официальная документация
- [FFmpeg Download](https://ffmpeg.org/download.html)
- [Supported Languages](https://github.com/openai/whisper#available-models-and-languages) 