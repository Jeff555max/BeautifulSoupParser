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

    print(f"Найденный токен: {token}")

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

    print(f"Запрашиваем URL: {table_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")

    # Получаем страницу с данными таблицы
    response = session.get(table_url, params=params)

    # Сохраняем HTML для анализа
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML-код страницы сохранен в файл debug_page.html")

    # Анализируем структуру страницы
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем все элементы, которые могут содержать данные
    print("\nАнализ структуры страницы:")

    # Проверяем наличие известных имен пользователей на странице
    page_text = soup.get_text()
    known_names = ['Иван', 'Петр', 'Василий', 'Алексей']
    found_names = [name for name in known_names if name in page_text]

    if found_names:
        print(f"На странице найдены имена пользователей: {', '.join(found_names)}")
    else:
        print("Имена пользователей не найдены на странице")

    # Ищем все таблицы на странице
    tables = soup.find_all('table')
    print(f"Всего найдено таблиц на странице: {len(tables)}")

    # Ищем все div элементы с классом, содержащим 'table'
    div_tables = soup.find_all('div', class_=lambda x: x and 'table' in x)
    print(f"Всего найдено div с классом, содержащим 'table': {len(div_tables)}")

    # Ищем все элементы с классом 'data'
    data_elements = soup.find_all(class_='data')
    print(f"Всего найдено элементов с классом 'data': {len(data_elements)}")

    # Ищем все элементы с id, содержащим 'table'
    id_tables = soup.find_all(id=lambda x: x and 'table' in x)
    print(f"Всего найдено элементов с id, содержащим 'table': {len(id_tables)}")

    # Проверяем наличие iframe (возможно данные загружаются в iframe)
    iframes = soup.find_all('iframe')
    print(f"Всего найдено iframe на странице: {len(iframes)}")

    # Ищем скрипты, которые могут загружать данные
    scripts = soup.find_all('script')
    print(f"Всего найдено скриптов на странице: {len(scripts)}")

    # Сохраняем содержимое всех таблиц для анализа
    for i, table in enumerate(tables):
        table_html = str(table)
        with open(f'table_{i + 1}.html', 'w', encoding='utf-8') as f:
            f.write(table_html)
        print(f"Таблица #{i + 1} сохранена в файл table_{i + 1}.html")

        # Проверяем наличие имен пользователей в этой таблице
        table_text = table.get_text()
        table_names = [name for name in known_names if name in table_text]
        if table_names:
            print(f"  В таблице #{i + 1} найдены имена: {', '.join(table_names)}")

    # Ищем данные в div элементах
    for i, div in enumerate(div_tables):
        div_html = str(div)
        with open(f'div_table_{i + 1}.html', 'w', encoding='utf-8') as f:
            f.write(div_html)
        print(f"Div с таблицей #{i + 1} сохранен в файл div_table_{i + 1}.html")

        # Проверяем наличие имен пользователей в этом div
        div_text = div.get_text()
        div_names = [name for name in known_names if name in div_text]
        if div_names:
            print(f"  В div #{i + 1} найдены имена: {', '.join(div_names)}")


if __name__ == "__main__":
    main()