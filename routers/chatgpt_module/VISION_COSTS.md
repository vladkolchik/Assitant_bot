# 💰 Vision API - Затраты и оптимизация

## 📊 **Стоимость изображений**

### **Базовая стоимость (январь 2025):**

| Модель | Цена за 1K токенов | Маленькое изображение (~85 токенов) | Большое изображение (~500+ токенов) |
|--------|-------------------|-----------------------------------|-----------------------------------|
| **gpt-4o-mini** | $0.00015 | ~$0.00001 | ~$0.00008 |
| **gpt-4o** | $0.0025 | ~$0.0002 | ~$0.001+ |
| **gpt-4-vision-preview** | $0.01 | ~$0.0008 | ~$0.005+ |

### **Факторы влияющие на стоимость:**

1. **Размер изображения** - основной фактор затрат
2. **Режим detail** - `low` vs `high`
3. **Количество изображений** в сообщении
4. **Модель ChatGPT** - разные цены за токен

---

## ⚙️ **Настройки оптимизации**

### **🔧 В файле `.env`:**

```env
# Экономичные настройки (рекомендуется):
VISION_ENABLED=true
VISION_DETAIL=low                    # ~85 токенов на изображение
MAX_IMAGE_SIZE_MB=5                  # Ограничение размера
AUTO_RESIZE_IMAGES=true              # Автосжатие
MAX_IMAGE_RESOLUTION=1024            # Сжимать большие изображения
SHOW_COST_WARNINGS=true              # Показывать стоимость

# Высокое качество (дорого!):
VISION_DETAIL=high                   # До 2000+ токенов на изображение
MAX_IMAGE_RESOLUTION=2048            # Больше деталей
```

### **🎯 Выбор модели:**

**Для экономии:**
```env
OPENAI_MODEL=gpt-4o-mini             # Самая дешевая с Vision
```

**Для качества:**
```env
OPENAI_MODEL=gpt-4o                  # Баланс цена/качество
```

---

## 🚨 **Потенциальные риски**

### **💸 Дорогие сценарии:**

1. **Множественные изображения высокого разрешения**
   - Стоимость: $0.01-0.05+ за изображение
   - Пример: 10 больших фото = $0.1-0.5

2. **Режим `detail=high` с большими изображениями**
   - 4K изображение = 2000+ токенов = $0.02-0.05

3. **Частое использование без лимитов**
   - 100 изображений/день = $1-10/день

### **🛡️ Защитные меры в модуле:**

✅ **Автоматическое сжатие** больших изображений  
✅ **Предупреждения о стоимости** перед обработкой  
✅ **Ограничения размера файла**  
✅ **Выбор режима качества**  
✅ **Точный расчет токенов**

---

## 📈 **Мониторинг затрат**

### **🔍 Проверка баланса OpenAI:**
1. Войдите на https://platform.openai.com/
2. Перейдите в **Billing** → **Usage**
3. Отслеживайте расход по API

### **📊 В боте:**
- Команда `/chatgpt_info` показывает настройки
- При отправке изображения видна приблизительная стоимость
- Логи содержат информацию о токенах

---

## 💡 **Рекомендации**

### **🏠 Для домашнего использования:**
```env
OPENAI_MODEL=gpt-4o-mini
VISION_DETAIL=low
MAX_IMAGE_SIZE_MB=5
SHOW_COST_WARNINGS=true
```
**Стоимость:** ~$0.00001-0.00008 за изображение

### **🏢 Для продакшена:**
```env
OPENAI_MODEL=gpt-4o
VISION_DETAIL=low
MAX_IMAGE_SIZE_MB=3
AUTO_RESIZE_IMAGES=true
MAX_IMAGE_RESOLUTION=800
```
**Стоимость:** ~$0.0002-0.001 за изображение

### **🎯 Для анализа высокого качества:**
```env
OPENAI_MODEL=gpt-4o
VISION_DETAIL=high
SHOW_COST_WARNINGS=true
# Используйте только для критических задач!
```
**Стоимость:** ~$0.001-0.01+ за изображение

---

## 🔧 **Устранение проблем**

### **❌ "Vision API отключен":**
1. Проверьте модель в `.env` - должна поддерживать Vision
2. Установите `VISION_ENABLED=true`
3. Проверьте что установлен Pillow: `pip install Pillow`

### **💸 Неожиданные затраты:**
1. Включите `SHOW_COST_WARNINGS=true`
2. Уменьшите `VISION_DETAIL` до `low`
3. Включите `AUTO_RESIZE_IMAGES=true`
4. Уменьшите `MAX_IMAGE_RESOLUTION`

### **🐌 Медленная обработка:**
1. Уменьшите размер изображений
2. Используйте `VISION_DETAIL=low`
3. Проверьте интернет соединение

---

## 📚 **Дополнительная информация**

- **OpenAI Pricing:** https://openai.com/pricing
- **Vision API Docs:** https://platform.openai.com/docs/guides/vision
- **Token Calculator:** https://platform.openai.com/tokenizer

**⚠️ Важно:** Цены могут изменяться. Всегда проверяйте актуальные тарифы на сайте OpenAI. 