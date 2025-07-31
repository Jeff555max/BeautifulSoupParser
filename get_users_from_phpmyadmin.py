import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import ssl
import os

# Отключение проверки SSL (если есть проблемы с сертификатом)
ssl._create_default_https_context = ssl._create_unverified_context

# Конфигурация
BASE_URL = 'http://185.244.219.162/phpmyadmin/'
LOGIN_URL = urljoin(BASE_URL, 'index.php')
DB_NAME = 'testDB'
TABLE_NAME = 'users'
USERNAME = 'test'
PASSWORD = 'JHFBdsyf2eg8*'

# Эмуляция браузера для Windows 11
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

session = requests.Session()


def save_debug_file(filename, content):
    """Сохраняет файл для отладки"""
    debug_dir = "debug"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    with open(os.path.join(debug_dir, filename), 'w', encoding='utf-8') as f:
        f.write(content)


try:
    # 1. Получаем начальную страницу для токена и кук
    print("1. Получение начальной страницы...")
    response = session.get(BASE_URL, headers=headers)
    response.raise_for_status()
    save_debug_file("initial_page.html", response.text)

    # 2. Анализ формы входа
    soup = BeautifulSoup(response.text, 'html.parser')
    login_form = soup.find('form', {'id': 'login_form'})
    if not login_form:
        raise Exception("Форма входа не найдена!")

    # Собираем ВСЕ скрытые поля формы
    form_data = {
        'pma_username': USERNAME,
        'pma_password': PASSWORD,
        'server': '1',
        'target': 'index.php'
    }

    for input_tag in login_form.find_all('input', type='hidden'):
        if input_tag.get('name') and input_tag.get('value'):
            form_data[input_tag['name']] = input_tag['value']

    print(f"2. Данные для авторизации: { {k: v for k, v in form_data.items() if k != 'pma_password'} }")

    # 3. Отправка формы входа
    print("3. Отправка данных авторизации...")
    auth_headers = headers.copy()
    auth_headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': BASE_URL,
        'Origin': BASE_URL
    })

    response = session.post(LOGIN_URL, headers=auth_headers, data=form_data)
    save_debug_file("auth_response.html", response.text)

    # 4. Проверка успешности авторизации
    if response.status_code != 200:
        raise Exception(f"HTTP ошибка: {response.status_code}")

    if 'mainFrameset' not in response.text and 'navigation.php' not in response.text:
        # Дополнительные проверки для диагностики
        if 'Access denied' in response.text:
            raise Exception("Доступ запрещён. Неверные учётные данные или IP заблокирован")
        elif 'Too many login' in response.text:
            raise Exception("Слишком много неудачных попыток входа")
        else:
            raise Exception("Неизвестная ошибка авторизации. Проверьте debug/auth_response.html")

    print("4. Авторизация успешна!")

    # Дальнейший код для получения данных таблицы...
    # (остаётся без изменений из предыдущего скрипта)

except Exception as e:
    print(f"Ошибка: {e}")
    print("\nРекомендации по диагностике:")
    print("1. Проверьте файлы в папке debug/")
    print("2. Попробуйте авторизоваться вручную через браузер")
    print("3. Проверьте правильность логина/пароля")
    print("4. Временно отключите антивирус и брандмауэр")
    exit(1)