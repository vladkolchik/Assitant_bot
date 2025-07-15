"""
Скрипт авторизации Google OAuth для email модуля
"""
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from pathlib import Path

# Скопы для Gmail API
SCOPES = ["https://mail.google.com/"]

def main():
    """Основная функция авторизации"""
    # Определяем папки для файлов
    auth_dir = Path(__file__).parent
    client_secret_file = auth_dir / "client_secret.json"
    token_file = auth_dir / "token.pkl"
    
    # Проверяем наличие client_secret.json
    if not client_secret_file.exists():
        # Проверяем в корне проекта (для обратной совместимости)
        root_client_secret = Path(__file__).parent.parent.parent.parent / "client_secret.json"
        if root_client_secret.exists():
            print(f"Найден client_secret.json в корне проекта: {root_client_secret}")
            print(f"Рекомендуется скопировать его в: {client_secret_file}")
            print("Продолжаем с файлом из корня...")
            client_secret_file = root_client_secret
        else:
            print(f"❌ Файл client_secret.json не найден!")
            print(f"Ожидаемое расположение: {client_secret_file}")
            print(f"Альтернативно: {root_client_secret}")
            print("\n📝 Инструкция:")
            print("1. Скачайте client_secret.json из Google Cloud Console")
            print("2. Поместите его в папку routers/email_router/auth/")
            print("3. Запустите скрипт заново")
            return
    
    print(f"🔐 Начинаем авторизацию Google OAuth...")
    print(f"📁 Файл конфигурации: {client_secret_file}")
    print(f"💾 Токен будет сохранен в: {token_file}")
    
    try:
        # Создаем flow для авторизации
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
        
        # Запускаем локальный сервер для авторизации
        print("\n🌐 Открываем браузер для авторизации...")
        creds = flow.run_local_server(port=0)
        
        # Сохраняем токен
        with open(token_file, "wb") as token_file_handle:
            pickle.dump(creds, token_file_handle)
        
        print(f"\n✅ Авторизация успешно завершена!")
        print(f"💾 Токен сохранен в: {token_file}")
        print(f"🚀 Теперь можно запускать бота: python bot.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка авторизации: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Убедитесь, что Gmail API включен в Google Cloud Console")
        print("2. Проверьте правильность client_secret.json")
        print("3. Добавьте свой email в тестеры проекта (OAuth consent screen)")

if __name__ == "__main__":
    main() 