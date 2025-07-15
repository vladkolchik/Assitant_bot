"""
Менеджер авторизации Google OAuth для email модуля
"""
import pickle
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GoogleAuthManager:
    """Менеджер для работы с Google OAuth авторизацией"""
    
    def __init__(self, auth_dir: str | None = None, email_address: str | None = None):
        """
        Инициализация менеджера авторизации
        
        Args:
            auth_dir: Директория для хранения файлов авторизации
                     По умолчанию - папка auth внутри текущего модуля
            email_address: Email адрес для авторизации (для логирования и валидации)
        """
        if auth_dir:
            self.auth_dir = Path(auth_dir)
        else:
            # Автоматически определяем папку auth текущего модуля
            self.auth_dir = Path(__file__).parent
        
        self.email_address = email_address
        self.token_file = self.auth_dir / "token.pkl"
        self.client_secret_file = self.auth_dir / "client_secret.json"
        
        # Создаем папку auth если её нет
        self.auth_dir.mkdir(exist_ok=True)
        
        logger.info(f"GoogleAuthManager initialized with auth_dir: {self.auth_dir}")
        if self.email_address:
            logger.info(f"Managing OAuth for email: {self.email_address}")
    
    def load_credentials(self):
        """Загружает credentials из файла"""
        try:
            with open(self.token_file, "rb") as token_file:
                return pickle.load(token_file)
        except FileNotFoundError:
            logger.error(f"Файл {self.token_file} не найден. Выполните авторизацию.")
            return None
        except Exception as e:
            logger.error(f"Ошибка загрузки {self.token_file}: {e}")
            return None
    
    def save_credentials(self, creds):
        """Сохраняет credentials в файл"""
        try:
            with open(self.token_file, "wb") as token_file:
                pickle.dump(creds, token_file)
            logger.info(f"Токен успешно сохранен в {self.token_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения токена: {e}")
    
    def ensure_valid_token(self, creds):
        """Обеспечивает валидность токена, обновляя его при необходимости"""
        if not creds:
            return None
        
        # Проверяем, нужно ли обновить токен
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Токен истек, обновляем...")
                    creds.refresh(Request())
                    self.save_credentials(creds)
                    logger.info("Токен успешно обновлен")
                except RefreshError as e:
                    logger.error(f"Не удалось обновить токен: {e}")
                    logger.error(f"Необходимо повторно выполнить авторизацию через {self.auth_dir}/script.py")
                    return None
            else:
                logger.error("Токен недействителен и не может быть обновлен")
                return None
        
        return creds
    
    def get_valid_credentials(self):
        """Получает валидные credentials, обновляя их при необходимости"""
        creds = self.load_credentials()
        return self.ensure_valid_token(creds)
    
    def is_authorized(self):
        """Проверяет, есть ли валидная авторизация"""
        creds = self.get_valid_credentials()
        return creds is not None and creds.valid
    
    def get_auth_status(self):
        """Возвращает статус авторизации с подробной информацией"""
        creds = self.load_credentials()
        if not creds:
            return {
                'is_authorized': False,
                'status': 'no_token',
                'message': f'Токен не найден. Выполните авторизацию через {self.auth_dir}/script.py'
            }
        
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                return {
                    'is_authorized': False,
                    'status': 'expired',
                    'message': 'Токен истек, требуется обновление'
                }
            else:
                return {
                    'is_authorized': False,
                    'status': 'invalid',
                    'message': f'Токен недействителен. Выполните авторизацию через {self.auth_dir}/script.py'
                }
        
        return {
            'is_authorized': True,
            'status': 'valid',
            'message': 'Авторизация действительна'
        } 