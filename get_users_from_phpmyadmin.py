import requests
from bs4 import BeautifulSoup
import csv
import os


def main():
    USERNAME = '****' # Введите Ваш логин
    PASSWORD = '***********' # Введите Ваш пароль

    session = requests.Session()

    # Получаем страницу входа для извлечения скрытых полей
    login_page_url = "http://185.244.219.162/phpmyadmin/index.php"
    response = session.get(login_page_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим форму входа
    login_form = soup.find('form', {'id': 'login_form'})
    if not login_form:
        print("Не удалось найти форму входа")
        return

    # Извлекаем все скрытые поля из формы
    hidden_fields = {}
    for hidden in login_form.find_all('input', {'type': 'hidden'}):
        if 'name' in hidden.attrs and 'value' in hidden.attrs:
            hidden_fields[hidden['name']] = hidden['value']

    # Добавляем учетные данные
    auth_data = {
        'pma_username': USERNAME,
        'pma_password': PASSWORD,
        'server': '1'
    }

    # Объединяем скрытые поля и учетные данные
    post_data = {**hidden_fields, **auth_data}

    # Определяем URL для отправки формы
    form_action = login_form.get('action', 'index.php')
    if form_action.startswith('/'):
        post_url = "http://185.244.219.162" + form_action
    else:
        post_url = "http://185.244.219.162/phpmyadmin/" + form_action

    # Выполняем авторизацию
    response = session.post(post_url, data=post_data)

    # Проверяем успешность авторизации по кукам
    if 'pmaAuth-1' not in session.cookies.get_dict():
        print("Ошибка авторизации! Куки аутентификации не установлены.")
        return

    print("Авторизация успешна!")

    # Получаем главную страницу для извлечения токена
    main_page = session.get("http://185.244.219.162/phpmyadmin/index.php")
    soup = BeautifulSoup(main_page.text, 'html.parser')

    # Ищем токен безопасности
    token = None
    token_input = soup.find('input', {'name': 'token'})
    if token_input:
        token = token_input['value']
    else:
        for hidden in soup.find_all('input', {'type': 'hidden'}):
            if hidden.get('name') == 'token':
                token = hidden['value']
                break

    if not token:
        print("Не удалось найти токен безопасности")
        return

    # Используем правильный URL для доступа к таблице users
    table_url = "http://185.244.219.162/phpmyadmin/index.php"

    # Параметры запроса для получения данных таблицы
    params = {
        'route': '/sql',
        'server': '1',
        'db': 'testDB',
        'table': 'users',
        'pos': '0',
        'token': token
    }

    # Получаем страницу с данными таблицы
    response = session.get(table_url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем таблицу с данными несколькими способами
    table = None

    # Способ 1: Поиск по id
    table = soup.find('table', {'id': 'table_results'})

    # Способ 2: Поиск по классу
    if not table:
        table = soup.find('table', {'class': 'data'})

    # Способ 3: Поиск по содержимому (ищем таблицу с известными именами пользователей)
    if not table:
        all_tables = soup.find_all('table')
        for t in all_tables:
            table_text = t.get_text()
            if any(name in table_text for name in ['Иван', 'Петр', 'Василий', 'Алексей']):
                table = t
                break

    # Способ 4: Поиск по классу Bootstrap
    if not table:
        table = soup.find('table', {'class': 'table table-striped table-hover'})

    if not table:
        print("Не удалось найти таблицу с данными")
        return

    # Извлекаем заголовки таблицы
    headers = []
    header_row = None

    # Ищем заголовки в thead
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')

    # Если thead нет, ищем первую строку таблицы
    if not header_row:
        header_row = table.find('tr')

    if header_row:
        for th in header_row.find_all(['th', 'td']):
            headers.append(th.get_text(strip=True))

    # Извлекаем строки данных
    data_rows = []
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')
        # Пропускаем заголовок, если он был найден
        if header_row and rows and rows[0] == header_row:
            rows = rows[1:]

    for row in rows:
        cells = row.find_all('td')
        row_data = [cell.get_text(strip=True) for cell in cells]
        if row_data:
            data_rows.append(row_data)

    # Выводим данные в консоль
    print("\nДанные из таблицы 'users':")
    if headers:
        print(" | ".join(headers))
        print("-" * 50)
    for row in data_rows:
        print(" | ".join(row))

    # Сохраняем данные в CSV файл (можно открыть в Excel)
    save_to_csv(headers, data_rows)

    # Сохраняем данные в Excel файл (требуется openpyxl)
    try:
        save_to_excel(headers, data_rows)
    except ImportError:
        print("\nДля сохранения в Excel установите библиотеку openpyxl: pip install openpyxl")


def save_to_csv(headers, data_rows):
    """Сохраняет данные в CSV файл"""
    filename = 'users_data.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        if headers:
            writer.writerow(headers)
        writer.writerows(data_rows)
    print(f"\nДанные сохранены в файл: {os.path.abspath(filename)}")


def save_to_excel(headers, data_rows):
    """Сохраняет данные в Excel файл"""
    try:
        import openpyxl
    except ImportError:
        raise ImportError("Библиотека openpyxl не установлена")

    filename = 'users_data.xlsx'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Users Data"

    # Записываем заголовки
    if headers:
        sheet.append(headers)

    # Записываем данные
    for row in data_rows:
        sheet.append(row)

    # Автоматическая ширина столбцов
    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[column_letter].width = adjusted_width

    workbook.save(filename)
    print(f"Данные сохранены в Excel файл: {os.path.abspath(filename)}")


if __name__ == "__main__":
    main()