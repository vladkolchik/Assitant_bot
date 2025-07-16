"""
Mem0 Memory Service для ChatGPT модуля
Управление долговременной памятью пользователей
"""
import os
import time
from typing import List, Dict, Optional, Union, Any

try:
    from mem0 import MemoryClient  # type: ignore
except ImportError:
    MemoryClient = None
    
from .config import MODULE_CONFIG

class Mem0MemoryService:
    """Сервис памяти на базе Mem0"""
    
    def __init__(self):
        # Получаем API ключ из переменных окружения
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key or MemoryClient is None:
            print("⚠️  MEM0_API_KEY не найден в .env или mem0 не установлен")
            print("📋 Добавьте MEM0_API_KEY=your-key в .env файл модуля")
            print("📋 Установите: pip install mem0ai")
            self.client = None
            self.enabled = False
        else:
            self.client = MemoryClient(api_key=api_key)
            self.enabled = True
            print("✅ Mem0 память инициализирована")
    
    async def add_conversation(self, user_id: str, messages: List[Dict[str, str]]) -> bool:
        """
        Добавляет диалог в память пользователя
        
        Args:
            user_id: ID пользователя Telegram
            messages: Список сообщений [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            bool: Успешно ли добавлено
        """
        if not self.enabled:
            return False
        
        try:
            # Добавляем в Mem0
            if self.client is None:
                return False
            result = self.client.add(messages, user_id=user_id)
            
            print(f"💾 Память обновлена для пользователя {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в Mem0: {e}")
            return False
    
    async def search_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> str:
        """
        Ищет релевантные воспоминания для текущего запроса
        
        Args:
            user_id: ID пользователя
            query: Текущий запрос/вопрос пользователя
            limit: Максимальное количество воспоминаний
        
        Returns:
            str: Отформатированный контекст из памяти
        """
        if not self.enabled or self.client is None:
            return ""
        
        try:
            # Ищем релевантные воспоминания
            memories = self.client.search(query, user_id=user_id, limit=limit)
            
            # print(f"🔍 ОТЛАДКА - Поиск по запросу '{query}' для пользователя {user_id}")
            # print(f"🔍 ОТЛАДКА - Найдено воспоминаний: {len(memories) if memories else 0}")
            
            # if memories:
            #     for i, memory in enumerate(memories):
            #         print(f"🔍 ОТЛАДКА - Воспоминание {i+1}: {memory}")
            
            if not memories:
                return ""
            
            # Форматируем контекст для ChatGPT
            context_parts = []
            for memory in memories:
                # Mem0 возвращает словарь с полем 'memory'
                memory_text = memory.get('memory', str(memory))
                context_parts.append(f"• {memory_text}")
            
            context = "Релевантная информация из предыдущих диалогов:\n" + "\n".join(context_parts)
            
            print(f"🔍 Найдено {len(memories)} релевантных воспоминаний для {user_id}")
            return context
            
        except Exception as e:
            print(f"❌ Ошибка поиска в Mem0: {e}")
            return ""
    
    async def get_user_profile(self, user_id: str) -> str:
        """
        Получает профиль пользователя из накопленной памяти
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Краткий профиль пользователя
        """
        if not self.enabled or self.client is None:
            return ""
        
        try:
            # Ищем общую информацию о пользователе
            profile_memories = self.client.search(
                "profile preferences about user", 
                user_id=user_id, 
                limit=10
            )
            
            if not profile_memories:
                return ""
            
            profile_parts = []
            for memory in profile_memories:
                memory_text = memory.get('memory', str(memory))
                profile_parts.append(memory_text)
            
            profile = "Информация о пользователе:\n" + "\n".join(profile_parts)
            return profile
            
        except Exception as e:
            print(f"❌ Ошибка получения профиля: {e}")
            return ""
    
    async def clear_user_memory(self, user_id: str) -> bool:
        """
        Очищает всю память пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Успешно ли очищено
        """
        if not self.enabled or self.client is None:
            return False
        
        try:
            # Mem0 API для удаления памяти пользователя
            self.client.delete_all(user_id=user_id)
            print(f"🗑️ Память пользователя {user_id} очищена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка очистки памяти: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования памяти"""
        if not self.enabled:
            return {"enabled": False, "error": "Mem0 не настроен"}
        
        try:
            # Получаем статистику (если API поддерживает)
            return {
                "enabled": True,
                "provider": "Mem0",
                "status": "Активно"
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}

# Глобальный экземпляр сервиса памяти
memory_service = Mem0MemoryService() 