"""
Гибридный Memory Service для ChatGPT модуля
Управление долговременной (Mem0) и сессионной (RAM) памятью пользователей
"""
import os
import time
from collections import defaultdict, deque
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

class HybridMemoryService:
    """Гибридный сервис памяти: объединяет Mem0 (долговременная) и RAM (сессионная)"""
    
    def __init__(self):
        self.mem0_service = Mem0MemoryService()
        # Сессионная память (в RAM, очищается при перезапуске)
        self.session_memory = defaultdict(lambda: deque(maxlen=10))  # Последние 10 пар диалогов
    
    # === СЕССИОННАЯ ПАМЯТЬ (RAM) ===
    
    def get_session_context(self, user_id: str, current_message: str = "") -> str:
        """Получает контекст из сессионной памяти"""
        history = list(self.session_memory.get(user_id, []))
        if not history:
            return ""
        
        # Берем последние 6 записей (3 пары диалогов)
        recent_history = history[-6:]
        context_lines = []
        
        for entry in recent_history:
            context_lines.append(entry)
        
        if context_lines:
            return "Контекст текущей беседы:\n" + "\n".join(context_lines)
        
        return ""
    
    def save_to_session_memory(self, user_id: str, user_message: str, ai_response: str):
        """Сохраняет диалог в сессионную память"""
        self.session_memory[user_id].append(f"👤: {user_message}")
        self.session_memory[user_id].append(f"🤖: {ai_response}")
    
    def clear_session_memory(self, user_id: str) -> bool:
        """Очищает сессионную память пользователя"""
        try:
            if user_id in self.session_memory:
                self.session_memory[user_id].clear()
            return True
        except Exception:
            return False
    
    def get_session_memory_stats(self, user_id: str) -> dict:
        """Возвращает статистику сессионной памяти"""
        history = self.session_memory.get(user_id, deque())
        return {
            'messages_count': len(history) // 2,  # Пары диалогов
            'total_entries': len(history),
            'max_capacity': getattr(history, 'maxlen', 10) or 10
        }
    
    # === ГИБРИДНЫЕ МЕТОДЫ ===
    
    async def get_full_context(self, user_id: str, query: str) -> tuple[str, int, str]:
        """
        Получает полный контекст из обеих систем памяти
        
        Returns:
            tuple: (combined_context, context_count, context_source)
        """
        context_parts = []
        context_count = 0
        context_source = ""
        
        if MODULE_CONFIG.get('mem0_enabled', False):
            # ГИБРИДНЫЙ РЕЖИМ: Mem0 + RAM
            
            # 1. Загружаем из Mem0 (семантический поиск)
            mem0_context = await self.mem0_service.search_relevant_memories(user_id, query, limit=3)
            mem0_profile = await self.mem0_service.get_user_profile(user_id)
            
            # 2. Загружаем из RAM (последние диалоги)
            session_context = self.get_session_context(user_id, query)
            
            # 3. Объединяем контексты
            if mem0_profile:
                context_parts.append(mem0_profile)
            if mem0_context:
                context_parts.append(mem0_context)
            if session_context:
                context_parts.append(session_context)
            
            combined_context = "\n\n".join(context_parts)
            
            if combined_context:
                # Подсчитываем общее количество элементов контекста
                mem0_count = len(mem0_context.split('\n')) - 1 if mem0_context else 0
                session_stats = self.get_session_memory_stats(user_id)
                session_count = session_stats['messages_count']
                
                context_count = mem0_count + session_count
                context_source = "гибридной"
                
            return combined_context, context_count, context_source
            
        else:
            # СЕССИОННАЯ ПАМЯТЬ: только RAM
            session_context = self.get_session_context(user_id, query)
            
            if session_context:
                session_stats = self.get_session_memory_stats(user_id)
                context_count = session_stats['messages_count']
                context_source = "сессионной"
                
            return session_context, context_count, context_source
    
    async def save_conversation(self, user_id: str, user_message: str, ai_response: str):
        """Сохраняет диалог в соответствующие системы памяти"""
        
        # Всегда сохраняем в сессионную память
        self.save_to_session_memory(user_id, user_message, ai_response)
        
        # Если включен Mem0 - сохраняем и туда
        if MODULE_CONFIG.get('mem0_enabled', False):
            conversation = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            await self.mem0_service.add_conversation(user_id, conversation)
    
    async def clear_all_memory(self, user_id: str) -> bool:
        """Очищает память во всех системах"""
        session_success = self.clear_session_memory(user_id)
        
        if MODULE_CONFIG.get('mem0_enabled', False):
            mem0_success = await self.mem0_service.clear_user_memory(user_id)
            return session_success and mem0_success
        
        return session_success
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Возвращает статистику текущего режима памяти"""
        if MODULE_CONFIG.get('mem0_enabled', False):
            # Гибридный режим
            mem0_stats = self.mem0_service.get_memory_stats()
            return {
                "mode": "hybrid",
                "enabled": True,
                "mem0_enabled": mem0_stats.get("enabled", False),
                "provider": "Mem0 + RAM",
                "description": "Гибридная память: семантический поиск (Mem0) + последние диалоги (RAM)"
            }
        else:
            # Только сессионная память
            return {
                "mode": "session",
                "enabled": True,
                "mem0_enabled": False,
                "provider": "RAM",
                "description": "Сессионная память: последние диалоги в оперативной памяти"
            }

# Глобальный экземпляр гибридного сервиса памяти
memory_service = HybridMemoryService() 