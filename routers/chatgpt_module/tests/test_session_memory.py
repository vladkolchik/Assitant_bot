#!/usr/bin/env python3
"""
Тест сессионной памяти ChatGPT модуля
Проверяет функциональность сохранения, получения и очистки сессионной памяти
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from routers.chatgpt_module.memory_service import HybridMemoryService

def test_session_memory():
    """Тестирует функциональность сессионной памяти"""
    print("🧪 Начинаю тест сессионной памяти...")
    
    # Создаем сервис памяти
    memory_service = HybridMemoryService()
    test_user_id = "test_user_123"
    
    print("\n1️⃣ Тест сохранения диалогов в сессионную память:")
    
    # Тестируем сохранение диалогов
    dialogues = [
        ("Привет!", "Привет! Как дела?"),
        ("Как тебя зовут?", "Меня зовут Ассистент."),
        ("Какая погода?", "Я не знаю, у меня нет доступа к данным о погоде."),
        ("Спасибо за помощь", "Пожалуйста! Обращайтесь если что-то нужно."),
    ]
    
    for user_msg, bot_response in dialogues:
        memory_service.save_to_session_memory(test_user_id, user_msg, bot_response)
        print(f"  ✅ Сохранен диалог: '{user_msg}' -> '{bot_response}'")
    
    print("\n2️⃣ Тест получения контекста сессионной памяти:")
    
    # Получаем контекст (только сессионная память)
    context = memory_service.get_session_context(test_user_id)
    print(f"  📝 Контекст из сессионной памяти ({len(context.split('\\n')) - 1} записей):")
    
    for line in context.split('\n'):
        if line.strip():
            print(f"    {line}")
    
    print("\n3️⃣ Тест статистики сессионной памяти:")
    
    # Получаем статистику
    stats = memory_service.get_session_memory_stats(test_user_id)
    print(f"  📊 Статистика: {stats}")
    
    print("\n4️⃣ Тест очистки сессионной памяти:")
    
    # Очищаем память
    memory_service.clear_session_memory(test_user_id)
    print("  🗑️ Сессионная память очищена")
    
    # Проверяем, что память действительно очищена
    context_after_clear = memory_service.get_session_context(test_user_id)
    stats_after_clear = memory_service.get_session_memory_stats(test_user_id)
    
    print(f"  📝 Контекст после очистки: '{context_after_clear}'")
    print(f"  📊 Статистика после очистки: {stats_after_clear}")
    
    if not context_after_clear and stats_after_clear['messages_count'] == 0:
        print("  ✅ Сессионная память успешно очищена")
    else:
        print("  ❌ Ошибка: память не была очищена полностью")
    
    print("\n🎉 Тест сессионной памяти завершен!")

if __name__ == "__main__":
    test_session_memory() 