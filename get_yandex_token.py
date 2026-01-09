# Файл: get_yandex_token.py
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_yandex_music_token():
    """
    Автоматизирует получение OAuth-токена для Яндекс.Музыки.
    Требует ручного ввода логина и пароля на странице авторизации Яндекса.
    """
    print("🚀 Запуск браузера для получения токена Яндекс.Музыки...")
    
    # Настройка Chrome для перехвата URL после редиректа
    options = webdriver.ChromeOptions()
    # Опция для предотвращения закрытия браузера после выполнения (удобно для отладки)
    # options.add_experimental_option("detach", True) 
    
    # Инициализация драйвера (убедитесь, что chromedriver установлен и в PATH)
    driver = webdriver.Chrome(options=options)
    
    # Формируем URL для запроса токена. Используется client_id официального приложения[citation:2].
    oauth_url = "https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d"
    driver.get(oauth_url)
    
    print("👤 Требуется ручная авторизация в Яндексе.")
    print("1. Введите логин и пароль в открывшемся окне браузера.")
    print("2. Подтвердите выдачу прав приложению (нажмите 'Разрешить').")
    print("3. Скрипт автоматически скопирует токен из адресной строки.")
    print("=" * 50)
    
    token = None
    previous_url = ""
    
    try:
        # Ожидаем, пока пользователь выполнит вход и произойдет редирект
        # Редирект будет на URL вида: https://music.yandex.ru/#access_token=AQAAAAA...&token_type=bearer...
        wait = WebDriverWait(driver, 300)  # Даем 5 минут на авторизацию
        
        # Ждем, пока URL изменится и будет содержать "access_token" или "error"
        def url_contains_token_or_error(driver):
            current_url = driver.current_url
            return "access_token=" in current_url or "error=" in current_url
        
        wait.until(url_contains_token_or_error)
        final_url = driver.current_url
        
        # Извлекаем токен из фрагмента URL (часть после #)
        if "access_token=" in final_url:
            # Разбираем URL, чтобы получить параметры после #
            fragment = final_url.split('#')[1]
            params = dict(param.split('=') for param in fragment.split('&'))
            token = params.get('access_token')
            
            if token:
                print("\n✅ Токен успешно получен!")
                print(f"🔑 Ваш токен: {token}")
                print("\n⚠️ Сохраните этот токен в .env файл вашего Telegram-бота как YANDEX_MUSIC_TOKEN.")
                print("Токен похож на длинную строку букв и цифр (например, AQAAAAA...).")
            else:
                print("❌ Не удалось найти access_token в URL.")
        elif "error=" in final_url:
            print(f"❌ Яндекс вернул ошибку: {final_url}")
            print("Попробуйте повторить процесс или используйте альтернативный метод.")
        else:
            print("❌ Не удалось определить результат авторизации.")
            
    except Exception as e:
        print(f"❌ Произошла ошибка во время выполнения: {e}")
    finally:
        # Даем пользователю время увидеть результат перед закрытием
        input("\nНажмите Enter для закрытия браузера...")
        driver.quit()
    
    return token

if __name__ == "__main__":
    token = get_yandex_music_token()
    if token:
        # Для удобства можно сразу записать токен в файл
        with open("token.txt", "w") as f:
            f.write(token)
        print("💾 Токен также сохранен в файл token.txt в текущей директории.")