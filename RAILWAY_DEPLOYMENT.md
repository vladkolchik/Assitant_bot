# 🚀 Развертывание Telegram бота на Railway (без Docker)

Этот гайд покажет, как развернуть Telegram бота с ChatGPT + Whisper на платформе Railway через GitHub напрямую, используя Nixpacks.

## 📋 Предварительные требования

1. **Аккаунт на Railway** - [зарегистрируйтесь](https://railway.app/)
2. **Telegram Bot Token** - создайте через [@BotFather](https://t.me/BotFather)
3. **OpenAI API Key** - получите на [platform.openai.com](https://platform.openai.com/api-keys)
4. **GitHub репозиторий** - форкните или склонируйте этот репозиторий

## 🔧 Пошаговое развертывание

### Шаг 1: Подготовка проекта

1. Убедитесь, что у вас есть все файлы:
   - `nixpacks.toml` ✅ (конфигурация сборки)
   - `railway.toml` ✅ (настройки Railway)
   - `requirements.txt` ✅ (Python зависимости)
   - `bot.py` ✅ (точка входа)

2. **Не нужны:** Docker файлы (Railway автоматически соберет проект)

### Шаг 2: Создание проекта на Railway

1. Войдите в [Railway Dashboard](https://railway.app/dashboard)
2. Нажмите **"New Project"**
3. Выберите **"Deploy from GitHub repo"**
4. Выберите ваш репозиторий
5. Railway автоматически определит Python проект и начнет сборку через Nixpacks

### Шаг 3: Настройка переменных окружения

В Railway Dashboard → Variables добавьте:

#### ✅ Обязательные переменные:
```bash
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENAI_API_KEY=sk-ваш_openai_api_key
```

#### 🎯 Рекомендуемые для o4-mini:
```bash
OPENAI_MODEL=o4-mini
OPENAI_MAX_COMPLETION_TOKENS=5000
WHISPER_MODE=api
WHISPER_LANGUAGE=auto
```

#### 📁 Настройки аудио:
```bash
MAX_AUDIO_SIZE_MB=25
MAX_AUDIO_DURATION_SEC=300
AUTO_CLEANUP_TEMP_FILES=true
```

### Шаг 4: Развертывание

1. Railway автоматически запустит сборку Docker образа
2. После успешной сборки бот будет развернут
3. Проверьте логи в разделе **"Deployments"**

## 🔍 Мониторинг и отладка

### Просмотр логов:
- Railway Dashboard → ваш проект → "Deployments" → "View Logs"

### Полезные команды для отладки:
```bash
# Проверка статуса FFmpeg (должен быть доступен)
ffmpeg -version

# Проверка переменных окружения
env | grep OPENAI
env | grep TELEGRAM
```

## 💰 Стоимость на Railway

**Railway Pricing (приблизительно):**
- **Hobby Plan**: $5/месяц + $0.000463/GB-час
- **Pro Plan**: $20/месяц + $0.000231/GB-час

**Примерная стоимость бота (Nixpacks эффективнее Docker):**
- CPU: ~0.05-0.1 vCPU × 24h × 30d = ~$2-4/месяц
- Memory: ~128-256MB RAM = минимальная стоимость
- **Итого: ~$7-9/месяц** (включая Railway план)

## 🎯 Оптимизация для Railway

### Минимизация ресурсов:
```bash
# В railway.toml или переменных окружения
WHISPER_MODE=api  # Используйте API вместо локального Whisper
AUTO_CLEANUP_TEMP_FILES=true  # Автоудаление временных файлов
MAX_AUDIO_SIZE_MB=25  # Ограничение размера аудио
```

### Мониторинг использования:
- Railway Dashboard → "Metrics" для просмотра CPU/Memory usage
- Оптимизируйте `OPENAI_MAX_COMPLETION_TOKENS` для экономии

## 🚨 Решение проблем

### Проблема: FFmpeg не найден
**Решение:** Убедитесь, что nixpacks.toml содержит FFmpeg в nixPkgs:
```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["python311", "ffmpeg"]
```

### Проблема: Ошибка Whisper language 'auto'
**Решение:** Уже исправлено в коде - 'auto' автоматически исключается для API

### Проблема: Превышение лимитов памяти
**Решение:** Используйте `WHISPER_MODE=api` вместо локального Whisper

## 📚 Дополнительные ресурсы

- [Railway Documentation](https://docs.railway.app/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи развертывания в Railway
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что Telegram Bot Token активен
4. Убедитесь, что OpenAI API Key имеет достаточный баланс

---

**🎉 Готово!** Ваш Telegram бот с ChatGPT + Whisper теперь работает на Railway! 