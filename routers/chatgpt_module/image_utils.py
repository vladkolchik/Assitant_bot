"""
Утилиты для обработки изображений в ChatGPT модуле
Включает сжатие, расчет затрат и подготовку для Vision API
"""
import base64
import io
import math
from typing import Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Класс для обработки изображений для Vision API"""
    
    def __init__(self, max_size_mb: int = 10, max_resolution: int = 1024, auto_resize: bool = True):
        self.max_size_mb = max_size_mb
        self.max_resolution = max_resolution
        self.auto_resize = auto_resize
    
    def estimate_tokens(self, width: int, height: int, detail: str = "low") -> int:
        """
        Оценка количества токенов для изображения
        
        Based on OpenAI documentation:
        - detail="low": ~85 tokens
        - detail="high": variable based on image size
        """
        if detail == "low":
            return 85
        
        # Для detail="high" расчет по формуле OpenAI
        # Изображение разбивается на тайлы 512x512
        tiles_width = math.ceil(width / 512)
        tiles_height = math.ceil(height / 512)
        total_tiles = tiles_width * tiles_height
        
        # Каждый тайл = 170 токенов + базовые 85 токенов
        tokens = total_tiles * 170 + 85
        return tokens
    
    def estimate_cost_usd(self, tokens: int, model: str = "gpt-4o") -> float:
        """
        Приблизительная стоимость в USD
        
        Цены на январь 2025 (за 1K токенов input):
        """
        # Цены за 1K токенов (input)
        prices = {
            "gpt-4o": 0.0025,
            "gpt-4o-mini": 0.00015,
            "gpt-4-vision-preview": 0.01,
            "gpt-4-turbo": 0.01,
        }
        
        # Определяем цену для модели
        price_per_1k = prices.get(model, 0.01)  # Fallback на самую дорогую
        
        return (tokens / 1000) * price_per_1k
    
    def resize_image(self, image_bytes: bytes, max_resolution: int) -> Tuple[bytes, int, int]:
        """
        Сжимает изображение до указанного разрешения с сохранением пропорций
        
        Returns:
            (resized_bytes, new_width, new_height)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_width, original_height = image.size
            
            # Определяем новые размеры с сохранением пропорций
            if max(original_width, original_height) <= max_resolution:
                # Изображение уже подходящего размера
                return image_bytes, original_width, original_height
            
            # Вычисляем новые размеры
            if original_width > original_height:
                new_width = max_resolution
                new_height = int((original_height * max_resolution) / original_width)
            else:
                new_height = max_resolution
                new_width = int((original_width * max_resolution) / original_height)
            
            # Сжимаем изображение
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Сохраняем в байты
            output_buffer = io.BytesIO()
            format_name = image.format or 'JPEG'
            if format_name == 'JPEG':
                resized_image.save(output_buffer, format=format_name, quality=85, optimize=True)
            else:
                resized_image.save(output_buffer, format=format_name, optimize=True)
            
            resized_bytes = output_buffer.getvalue()
            output_buffer.close()
            
            logger.info(f"Изображение сжато: {original_width}x{original_height} → {new_width}x{new_height}")
            return resized_bytes, new_width, new_height
            
        except Exception as e:
            logger.error(f"Ошибка сжатия изображения: {e}")
            # Возвращаем оригинал в случае ошибки
            try:
                image = Image.open(io.BytesIO(image_bytes))
                return image_bytes, image.size[0], image.size[1]
            except:
                # Если даже это не работает, возвращаем дефолтные значения
                return image_bytes, 1024, 1024
    
    def prepare_image_for_api(self, image_bytes: bytes, detail: str = "low") -> Tuple[str, dict]:
        """
        Подготавливает изображение для отправки в Vision API
        
        Returns:
            (base64_image, image_info_dict)
        """
        try:
            # Получаем размеры оригинального изображения
            original_image = Image.open(io.BytesIO(image_bytes))
            original_width, original_height = original_image.size
            original_size_mb = len(image_bytes) / (1024 * 1024)
            
            # Определяем, нужно ли сжимать
            processed_bytes = image_bytes
            final_width, final_height = original_width, original_height
            was_resized = False
            
            if self.auto_resize and original_size_mb > self.max_size_mb:
                processed_bytes, final_width, final_height = self.resize_image(
                    image_bytes, self.max_resolution
                )
                was_resized = True
            elif self.auto_resize and max(original_width, original_height) > self.max_resolution:
                processed_bytes, final_width, final_height = self.resize_image(
                    image_bytes, self.max_resolution
                )
                was_resized = True
            
            # Кодируем в base64
            base64_image = base64.b64encode(processed_bytes).decode('utf-8')
            
            # Рассчитываем токены и стоимость
            estimated_tokens = self.estimate_tokens(final_width, final_height, detail)
            
            # Информация об изображении
            image_info = {
                'original_size': f"{original_width}x{original_height}",
                'final_size': f"{final_width}x{final_height}",
                'was_resized': was_resized,
                'original_size_mb': round(original_size_mb, 2),
                'final_size_mb': round(len(processed_bytes) / (1024 * 1024), 2),
                'estimated_tokens': estimated_tokens,
                'detail': detail,
            }
            
            return base64_image, image_info
            
        except Exception as e:
            logger.error(f"Ошибка подготовки изображения: {e}")
            raise
    
    def get_cost_warning(self, image_info: dict, model: str = "gpt-4o") -> str:
        """
        Формирует предупреждение о затратах
        """
        estimated_cost = self.estimate_cost_usd(image_info['estimated_tokens'], model)
        
        warning = f"💰 **Приблизительная стоимость:** ~${estimated_cost:.4f}\n"
        warning += f"🎯 **Токенов:** ~{image_info['estimated_tokens']}\n"
        warning += f"📏 **Размер:** {image_info['final_size']}"
        
        if image_info['was_resized']:
            warning += f" (сжато с {image_info['original_size']})"
        
        if image_info['detail'] == "high":
            warning += f"\n⚠️ **Высокое качество** - может быть дороже!"
        
        return warning

def create_image_processor(config: dict) -> ImageProcessor:
    """Создает ImageProcessor из конфигурации модуля"""
    return ImageProcessor(
        max_size_mb=config['max_image_size_mb'],
        max_resolution=config['max_image_resolution'],
        auto_resize=True  # Автоматическое изменение размера всегда включено
    ) 