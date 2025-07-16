#!/usr/bin/env python3
"""
Тест гибридной памяти ChatGPT модуля
Проверяет функциональность объединения Mem0 и сессионной памяти
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from routers.chatgpt_module.memory_service import HybridMemoryService
from routers.chatgpt_module.config import MODULE_CONFIG

async def test_hybrid_memory():
    """Тестирует функциональность гибридной памяти"""
    print("🧪 Начинаю тест гибридной памяти...")
    
    # Создаем сервис памяти
    memory_service = HybridMemoryService()
    test_user_id = "test_user_456"
    
    print(f"\n📊 Текущий режим памяти: {MODULE_CONFIG.get('mem0_enabled', False)}")
    stats = memory_service.get_memory_stats()
    print(f"📊 Статистика системы: {stats}")
    
    print("\n1️⃣ Тест сохранения диалогов в гибридную память:")
    
    # Тестируем сохранение диалогов
    dialogues = [
        ("Меня зовут Алексей", "Приятно познакомиться, Алексей!"),
        ("Я работаю программистом", "Здорово! Какими языками программирования пользуетесь?"),
        ("Использую Python и JavaScript", "Отличный выбор! Это очень популярные языки."),
        ("Какая погода сегодня?", "Я не могу узнать текущую погоду, но могу помочь с другими вопросами."),
        ("Спасибо за помощь", "Пожалуйста! Всегда рад помочь, Алексей."),
    ]
    
    for user_msg, bot_response in dialogues:
        await memory_service.save_conversation(test_user_id, user_msg, bot_response)
        print(f"  ✅ Сохранен диалог: '{user_msg}' -> '{bot_response}'")
    
    print("\n2️⃣ Тест получения полного контекста:")
    
    # Тестируем разные запросы для поиска контекста
    test_queries = [
        "Как меня зовут?",
        "Какая у меня профессия?",
        "Что я говорил о программировании?",
        "Общий разговор"
    ]
    
    for query in test_queries:
        print(f"\n  🔍 Запрос: '{query}'")
        context, count, source = await memory_service.get_full_context(test_user_id, query)
        
        if context:
            print(f"  📝 Найдено контекста: {count} элементов из {source} памяти")
            # Показываем только первые 2 строки для краткости
            context_lines = context.split('\n')[:3]
            for line in context_lines:
                if line.strip():
                    print(f"    {line[:100]}{'...' if len(line) > 100 else ''}")
        else:
            print(f"  📝 Контекст не найден")
    
    print("\n3️⃣ Тест статистики памяти:")
    
    # Сессионная статистика
    session_stats = memory_service.get_session_memory_stats(test_user_id)
    print(f"  📊 Сессионная память: {session_stats}")
    
    # Общая статистика системы
    system_stats = memory_service.get_memory_stats()
    print(f"  📊 Система памяти: {system_stats}")
    
    print("\n4️⃣ Тест очистки гибридной памяти:")
    
    # Очищаем всю память
    success = await memory_service.clear_all_memory(test_user_id)
    print(f"  🗑️ Очистка памяти: {'успешно' if success else 'ошибка'}")
    
    # Проверяем результат очистки
    context_after_clear, count_after, source_after = await memory_service.get_full_context(test_user_id, "тест")
    session_stats_after = memory_service.get_session_memory_stats(test_user_id)
    
    print(f"  📝 Контекст после очистки: {'пуст' if not context_after_clear else 'остался'}")
    print(f"  📊 Сессионная статистика: {session_stats_after}")
    
    if not context_after_clear and session_stats_after['messages_count'] == 0:
        print("  ✅ Гибридная память успешно очищена")
    else:
        print("  ⚠️  Память очищена частично (это нормально для Mem0)")
    
    print("\n🎉 Тест гибридной памяти завершен!")

if __name__ == "__main__":
    asyncio.run(test_hybrid_memory()) 