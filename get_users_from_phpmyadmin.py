import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

# Конфигурация
BASE_URL = 'http://185.244.219.162/phpmyadmin/'
LOGIN_URL = urljoin(BASE_URL, 'index.php')
DB_NAME = 'testDB'
TABLE_NAME = 'users'
USERNAME = 'test'
PASSWORD = 'JHFBdsyf2eg8*'

# Эмуляция браузера
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

session = requests.Session()

# 1. Авторизация
print("Авторизация...")

# Данные для авторизации
login_data = {
    'pma_username': USERNAME,
    'pma_password': PASSWORD,
    'server': '1',
    'target': 'index.php'
}

# Добавляем заголовки для авторизации
auth_headers = headers.copy()
auth_headers['Content-Type'] = 'application/x-www-form-urlencoded'

# Отправляем запрос на авторизацию
try:
    response = session.post(LOGIN_URL, headers=auth_headers, data=login_data)
    response.raise_for_status()  # Проверяем на ошибки HTTP

    # Проверяем успешность авторизации
    if 'phpMyAdmin' not in response.text:
        print("Авторизация не удалась!")
        exit(1)

    # Получаем куки после авторизации
    print("\nПолученные куки:")
    for cookie in session.cookies:
        print(f"{cookie.name}: {cookie.value}")

    # Переходим к базе данных
    print("\nПереходим к базе данных...")
    db_url = urljoin(BASE_URL, f'index.php?route=/database/structure&db={DB_NAME}')
    response = session.get(db_url, headers=headers)
    response.raise_for_status()

    # 2. Переходим к странице с данными
    print("Переходим к странице с данными...")
    data_url = urljoin(BASE_URL, f'index.php?route=/sql&db={DB_NAME}&table={TABLE_NAME}&pos=0')

    # Добавляем заголовки для прямого запроса
    data_headers = headers.copy()
    data_headers.update({
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'text/html, */*; q=0.01',
        'Referer': urljoin(BASE_URL, f'index.php?route=/database/structure&db={DB_NAME}')
    })

    print(f"\nОтправляем запрос к URL: {data_url}")
    response = session.get(data_url, headers=data_headers)
    response.raise_for_status()

    print(f"\nСтатус ответа: {response.status_code}")
    print(f"Длина ответа: {len(response.text)} символов")

    # Проверяем успешность получения данных
    if 'Error' in response.text or 'Ошибка' in response.text:
        print("Ошибка при получении данных!")
        print("\nТекст ответа:")
        print(response.text[:500])  # Показываем первые 500 символов для отладки
        with open('error.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        exit(1)

    # Сохраняем ответ для отладки
    with open('response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    # 4. Парсим HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Проверяем структуру страницы
    print("\nСтруктура страницы:")
    print("Заголовок страницы:", soup.title.string if soup.title else "Нет заголовка")

    # Ищем все таблицы на странице
    tables = soup.find_all('table')
    print(f"\nНайдено таблиц: {len(tables)}")

    # Проверяем классы таблиц
    for i, table in enumerate(tables, 1):
        classes = table.get('class', [])
        print(f"Таблица {i}: классы = {classes}")
        # Проверяем содержимое таблицы
        print(f"Таблица {i} содержит:")
        print(f"Заголовки: {[th.get_text(strip=True) for th in table.find_all('th')]}")
        print(f"Строки: {len(table.find_all('tr'))}")

    # Ищем нужную таблицу
    possible_classes = ['table_results', 'table', 'table-striped', 'table-hover', 'table-condensed', 'table-bordered']
    target_table = None
    for cls in possible_classes:
        target_table = soup.find('table', class_=cls)
        if target_table:
            print(f"Найдена таблица с классом: {cls}")
            break

    if not target_table:
        print("Не найдена таблица с данными!")
        # Сохраняем HTML для анализа
        with open('debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        exit(1)

    # Проверяем структуру найденной таблицы
    print("\nСтруктура найденной таблицы:")
    headers = [th.get_text(strip=True) for th in target_table.find_all('th')]
    print("Заголовки:", headers)
    print("Количество строк:", len(target_table.find_all('tr')))

    # Проверяем содержимое первой строки
    first_row = target_table.find('tr')
    if first_row:
        print("Содержимое первой строки:", [td.get_text(strip=True) for td in first_row.find_all('td')])

    # 5. Извлекаем данные
    thead = target_table.find('thead')
    tbody = target_table.find('tbody')

    if not thead or not tbody:
        print("Таблица не содержит thead или tbody!")
        exit(1)

    headers = [th.get_text(strip=True) for th in thead.find_all('th')]
    rows = []

    for tr in tbody.find_all('tr'):
        row_data = [td.get_text(strip=True) for td in tr.find_all('td')]
        if row_data:
            row_dict = dict(zip(headers, row_data))
            rows.append(row_dict)

    if not rows:
        print("Таблица пустая!")
        exit(1)

    # 6. Выводим и сохраняем результаты
    print("\nДанные из таблицы users:")
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    df.to_excel('users_from_phpmyadmin.xlsx', index=False)
    print("\nДанные успешно сохранены в файл users_from_phpmyadmin.xlsx")

    # 7. Сохраняем полный HTML для отладки
    with open('page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Сохранена страница для отладки: page.html")

except requests.exceptions.RequestException as e:
    print(f"Ошибка при выполнении запроса: {e}")
    exit(1)
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
    exit(1)