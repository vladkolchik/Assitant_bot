"""
Сервисы email модуля - модульный подход
"""
import base64
import smtplib
import logging
from email.message import EmailMessage
from .config import GMAIL_ADDRESS, EMAIL_CONFIG
from .auth import GoogleAuthManager

# Настройка логирования для email модуля
logger = logging.getLogger(__name__)

# Инициализируем менеджер авторизации с конфигурацией модуля
auth_manager = GoogleAuthManager(email_address=GMAIL_ADDRESS)

class EmailSenderError(Exception):
    """Базовое исключение для ошибок отправки email"""
    pass

class AuthenticationError(EmailSenderError):
    """Ошибка авторизации"""
    pass

class SMTPConnectionError(EmailSenderError):
    """Ошибка подключения к SMTP"""
    pass

def send_email_oauth2(recipient, subject, body, attachments=None):
    """
    Отправка email через Gmail OAuth2
    
    Args:
        recipient: Email получателя
        subject: Тема письма
        body: Тело письма
        attachments: Список файлов для прикрепления (опционально)
        
    Returns:
        tuple: (success: bool, error_message: str | None)
    """
    try:
        # Получаем валидные credentials через менеджер авторизации
        creds = auth_manager.get_valid_credentials()
        if not creds:
            auth_status = auth_manager.get_auth_status()
            return False, f"Ошибка авторизации: {auth_status['message']}"
        
        # Создаем сообщение
        message = EmailMessage()
        message["From"] = GMAIL_ADDRESS
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        
        # Добавляем вложения, если есть
        if attachments:
            for file_name, file_data in attachments:
                try:
                    # file_data уже содержит байты файла, не нужно читать с диска
                    if not isinstance(file_data, bytes):
                        error_msg = f"Неверный тип данных для файла {file_name}: ожидались bytes"
                        logger.error(error_msg)
                        return False, error_msg
                    
                    # Определяем MIME тип на основе расширения файла
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(file_name)
                    if mime_type:
                        maintype, subtype = mime_type.split('/', 1)
                    else:
                        maintype = "application"
                        subtype = "octet-stream"
                    
                    # Добавляем файл как вложение
                    message.add_attachment(
                        file_data,
                        maintype=maintype,
                        subtype=subtype,
                        filename=file_name
                    )
                    logger.info(f"Добавлено вложение: {file_name} ({len(file_data)} байт)")
                    
                except Exception as e:
                    error_msg = f"Ошибка добавления вложения {file_name}: {e}"
                    logger.error(error_msg)
                    return False, error_msg
        
        # Подключаемся к Gmail SMTP (используем проверенный метод)
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()  # Команда приветствия SMTP
                server.starttls()  # Включаем TLS
                
                # Аутентифицируемся с помощью OAuth2 (проверенный формат)
                auth_string = f"user={GMAIL_ADDRESS}\x01auth=Bearer {creds.token}\x01\x01"
                auth_bytes = base64.b64encode(auth_string.encode("utf-8"))
                server.docmd("AUTH", "XOAUTH2 " + auth_bytes.decode())
                
                # Отправляем письмо
                server.send_message(message)
                
                logger.info(f"Email успешно отправлен на {recipient}")
                return True, None
                
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Ошибка аутентификации SMTP: {e}"
            logger.error(error_msg)
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"Ошибка SMTP: {e}"
            logger.error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Неожиданная ошибка при отправке email: {e}"
        logger.error(error_msg)
        return False, error_msg

def get_auth_status():
    """Возвращает статус авторизации"""
    return auth_manager.get_auth_status()

def is_authorized():
    """Проверяет, авторизован ли пользователь"""
    return auth_manager.is_authorized() 