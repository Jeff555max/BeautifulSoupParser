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

session = requests.Session()

# 1. Получаем токен с главной страницы (phpMyAdmin использует CSRF)
resp = session.get(LOGIN_URL)
soup = BeautifulSoup(resp.text, 'html.parser')
token_input = soup.find('input', {'name': 'token'})
token = token_input['value'] if token_input else ''

# 2. Авторизация
login_data = {
    'pma_username': USERNAME,
    'pma_password': PASSWORD,
    'server': 1,
    'target': 'index.php',
    'token': token
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': LOGIN_URL,
    'Origin': BASE_URL,
}
resp = session.post(LOGIN_URL, data=login_data, headers=headers, allow_redirects=True)

# Проверяем успешность входа
if 'logout.php' not in resp.text:
    print('Ошибка авторизации!')
    exit(1)

# 3. Переходим на страницу с таблицей users (просмотр содержимого)
table_url = urljoin(BASE_URL, f'tbl_select.php?db={DB_NAME}&table={TABLE_NAME}')
resp = session.get(table_url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

# 4. Ищем таблицу с id="table_results" (основная таблица с данными)
table = soup.find('table', {'id': 'table_results'})
if not table:
    print('Не найдена таблица с id="table_results"!')
    exit(1)

# 5. Получаем заголовки и строки
headers_row = table.find('thead').find_all('th')
headers_text = [th.get_text(strip=True) for th in headers_row]

# Определяем индексы нужных столбцов
try:
    id_idx = headers_text.index('id')
    name_idx = headers_text.index('name')
except ValueError:
    print('Не найдены нужные столбцы (id, name) в заголовках!')
    exit(1)

rows = []
for tr in table.find('tbody').find_all('tr'):
    tds = tr.find_all('td')
    if len(tds) > max(id_idx, name_idx):
        row = [td.get_text(strip=True) for td in tds]
        rows.append({'id': row[id_idx], 'name': row[name_idx]})

if not rows:
    print('Нет данных в таблице users!')
    exit(1)

df = pd.DataFrame(rows)
print('Результаты парсинга:')
print(df.to_string(index=False))
df.to_excel('users_from_phpmyadmin.xlsx', index=False)
print('Данные успешно сохранены в users_from_phpmyadmin.xlsx') 