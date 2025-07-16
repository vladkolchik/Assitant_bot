#!/usr/bin/env python3
"""
Запуск всех тестов памяти ChatGPT модуля
Удобный способ проверить всю функциональность сразу
"""

import sys
import os
import asyncio
import traceback
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

async def run_all_tests():
    """Запускает все тесты памяти"""
    print("🚀 Запуск полного тестирования памяти ChatGPT модуля")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Список тестов для запуска
    tests = [
        ("Сессионная память", "test_session_memory"),
        ("Гибридная память", "test_hybrid_memory"),
        ("Переключение режимов", "test_memory_toggle")
    ]
    
    results = {}
    
    for test_name, test_module in tests:
        print(f"\n🧪 ЗАПУСК ТЕСТА: {test_name}")
        print("-" * 40)
        
        try:
            # Динамический импорт и запуск теста
            if test_module == "test_session_memory":
                from test_session_memory import test_session_memory
                test_session_memory()
                results[test_name] = "✅ УСПЕШНО"
                
            elif test_module == "test_hybrid_memory":
                from test_hybrid_memory import test_hybrid_memory
                await test_hybrid_memory()
                results[test_name] = "✅ УСПЕШНО"
                
            elif test_module == "test_memory_toggle":
                from test_memory_toggle import test_memory_toggle
                await test_memory_toggle()
                results[test_name] = "✅ УСПЕШНО"
                
        except Exception as e:
            print(f"❌ ОШИБКА В ТЕСТЕ {test_name}:")
            print(f"   {str(e)}")
            print(f"   Трейс: {traceback.format_exc()}")
            results[test_name] = f"❌ ОШИБКА: {str(e)}"
        
        print("-" * 40)
    
    # Итоговые результаты
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results.items():
        print(f"{result:<30} {test_name}")
        if "✅" in result:
            success_count += 1
    
    print("-" * 60)
    print(f"🎯 Успешных тестов: {success_count}/{len(tests)}")
    print(f"📅 Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(tests):
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        traceback.print_exc() 