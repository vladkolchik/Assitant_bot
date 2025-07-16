#!/usr/bin/env python3
"""
Тест переключения режимов памяти ChatGPT модуля
Проверяет функциональность переключения между гибридным и сессионным режимами
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from routers.chatgpt_module.memory_service import HybridMemoryService
from routers.chatgpt_module.config import MODULE_CONFIG
from routers.chatgpt_module.router import toggle_mem0_setting

async def test_memory_toggle():
    """Тестирует переключение режимов памяти"""
    print("🧪 Начинаю тест переключения режимов памяти...")
    
    # Создаем сервис памяти
    memory_service = HybridMemoryService()
    test_user_id = "test_user_toggle"
    
    # Сохраняем изначальное состояние
    original_state = MODULE_CONFIG.get('mem0_enabled', False)
    print(f"\n📊 Изначальный режим: {'Гибридный' if original_state else 'Сессионный'}")
    
    print("\n1️⃣ Тест работы в текущем режиме:")
    
    # Добавляем тестовый диалог
    await memory_service.save_conversation(test_user_id, "Тест сохранения", "Диалог сохранен")
    
    # Проверяем контекст
    context, count, source = await memory_service.get_full_context(test_user_id, "тест")
    print(f"  📝 Контекст в {source} режиме: {count} элементов")
    
    # Получаем статистику
    stats_before = memory_service.get_memory_stats()
    print(f"  📊 Статистика до переключения: {stats_before}")
    
    print("\n2️⃣ Тест переключения режима:")
    
    # Переключаем режим
    new_state = await toggle_mem0_setting()
    
    print(f"  🔄 Переключено на: {'Гибридный' if new_state else 'Сессионный'}")
    print(f"  📊 MEM0_ENABLED = {MODULE_CONFIG.get('mem0_enabled', False)}")
    
    # Проверяем новую статистику
    stats_after = memory_service.get_memory_stats()
    print(f"  📊 Статистика после переключения: {stats_after}")
    
    print("\n3️⃣ Тест работы в новом режиме:")
    
    # Добавляем еще один диалог
    await memory_service.save_conversation(test_user_id, "Второй тест", "Работает в новом режиме")
    
    # Проверяем контекст в новом режиме
    context_new, count_new, source_new = await memory_service.get_full_context(test_user_id, "тест")
    print(f"  📝 Контекст в {source_new} режиме: {count_new} элементов")
    
    # Проверяем сессионную статистику
    session_stats = memory_service.get_session_memory_stats(test_user_id)
    print(f"  📊 Сессионная статистика: {session_stats}")
    
    print("\n4️⃣ Тест восстановления изначального режима:")
    
    # Возвращаем изначальное состояние
    if MODULE_CONFIG.get('mem0_enabled', False) != original_state:
        await toggle_mem0_setting()
        print(f"  🔄 Восстановлен изначальный режим: {'Гибридный' if original_state else 'Сессионный'}")
    else:
        print(f"  ✅ Режим уже соответствует изначальному")
    
    # Финальная проверка
    final_stats = memory_service.get_memory_stats()
    print(f"  📊 Финальная статистика: {final_stats}")
    
    print("\n5️⃣ Очистка тестовых данных:")
    
    # Очищаем тестовые данные
    success = await memory_service.clear_all_memory(test_user_id)
    print(f"  🗑️ Очистка: {'успешно' if success else 'ошибка'}")
    
    print("\n🎉 Тест переключения режимов завершен!")
    print(f"📊 Восстановлен режим: {'Гибридный' if MODULE_CONFIG.get('mem0_enabled', False) else 'Сессионный'}")

if __name__ == "__main__":
    asyncio.run(test_memory_toggle()) 