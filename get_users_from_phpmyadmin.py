import requests
from bs4 import BeautifulSoup


def main():
    USERNAME = 'test'
    PASSWORD = 'JHFBdsyf2eg8*'

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

    print(f"Отправляем запрос на: {post_url}")

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

    # URL для доступа к таблице users
    table_url = "http://185.244.219.162/phpmyadmin/sql.php"

    # Параметры запроса для получения данных таблицы
    params = {
        'db': 'testDB',
        'table': 'users',
        'pos': 0,
        'token': token,
        'server': '1'
    }

    # Получаем страницу с данными таблицы
    response = session.get(table_url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем таблицу с данными
    table = soup.find('table', {'id': 'table_results'})
    if not table:
        table = soup.find('table', {'class': 'data'})
    if not table:
        print("Не удалось найти таблицу с данными")
        return

    # Извлекаем заголовки таблицы
    headers = []
    header_row = table.find('thead')
    if header_row:
        header_row = header_row.find('tr')
    else:
        header_row = table.find('tr')

    if header_row:
        for th in header_row.find_all('th'):
            headers.append(th.get_text(strip=True))

    # Извлекаем строки данных
    data_rows = []
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')
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


if __name__ == "__main__":
    main()