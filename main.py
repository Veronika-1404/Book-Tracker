import PySimpleGUI as sg
import json
import os
import subprocess

# Файл для хранения данных
DATA_FILE = 'books.json'

# Функция загрузки данных из JSON с обработкой ошибок
def load_books():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Проверяем, что загруженные данные — это список
                if isinstance(data, list):
                    return data
                else:
                    sg.popup('Предупреждение', 'Файл books.json повреждён. Создан новый список книг.')
                    return []
        except json.JSONDecodeError:
            sg.popup('Предупреждение', 'Файл books.json пуст или повреждён. Создан новый список книг.')
            return []
    return []

# Функция сохранения данных в JSON
def save_books(books):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)
    # Автокоммит в Git
    try:
        subprocess.run(['git', 'add', DATA_FILE], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update books list'], check=True)
    except subprocess.CalledProcessError:
        pass  # Git не настроен или нет изменений

# Инициализация Git (если не инициализирован)
if not os.path.exists('.git'):
    try:
        subprocess.run(['git', 'init'], check=True)
        with open('.gitignore', 'w') as f:
            f.write('__pycache__/\n')
    except:
        pass

# Загрузка существующих книг
books = load_books()

# Макет интерфейса
layout = [
    [sg.Text('Название книги:'), sg.Input(key='-TITLE-')],
    [sg.Text('Автор:'), sg.Input(key='-AUTHOR-')],
    [sg.Text('Жанр:'), sg.Input(key='-GENRE-')],
    [sg.Text('Количество страниц:'), sg.Input(key='-PAGES-')],
    [sg.Button('Добавить книгу'), sg.Button('Сохранить'), sg.Button('Загрузить')],
    [sg.Text('Фильтр по жанру:'), sg.Input(key='-FILTER_GENRE-'),
     sg.Text('Страницы >'), sg.Input(key='-FILTER_PAGES-', size=(10, 1))],
    [sg.Table(
        values=[[b['title'], b['author'], b['genre'], b['pages']] for b in books],
        headings=['Название', 'Автор', 'Жанр', 'Страниц'],
        key='-TABLE-',
        enable_events=True,
        justification='left'
    )]
]

# Создание окна
window = sg.Window('Book Tracker', layout)

# Основной цикл обработки событий
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == 'Добавить книгу':
        # Валидация ввода
        title = values['-TITLE-'].strip()
        author = values['-AUTHOR-'].strip()
        genre = values['-GENRE-'].strip()
        pages_str = values['-PAGES-'].strip()

        if not title or not author or not genre:
            sg.popup('Ошибка', 'Все поля, кроме фильтра, должны быть заполнены!')
            continue

        try:
            pages = int(pages_str)
            if pages <= 0:
                raise ValueError
        except ValueError:
            sg.popup('Ошибка', 'Количество страниц должно быть положительным числом!')
            continue

        # Добавление книги
        book = {
            'title': title,
            'author': author,
            'genre': genre,
            'pages': pages
        }
        books.append(book)

        # Обновление таблицы
        window['-TABLE-'].update(
            values=[[b['title'], b['author'], b['genre'], b['pages']] for b in books]
        )

        # Очистка полей ввода
        window['-TITLE-'].update('')
        window['-AUTHOR-'].update('')
        window['-GENRE-'].update('')
        window['-PAGES-'].update('')

    elif event in ('Добавить книгу', 'Сохранить', 'Загрузить', '-FILTER_GENRE-', '-FILTER_PAGES-'):
        # Фильтрация
        filter_genre = values['-FILTER_GENRE-'].strip().lower()
        filter_pages_str = values['-FILTER_PAGES-'].strip()

        filtered_books = books
        if filter_genre:
            filtered_books = [b for b in filtered_books if filter_genre in b['genre'].lower()]
        if filter_pages_str:
            try:
                min_pages = int(filter_pages_str)
                filtered_books = [b for b in filtered_books if b['pages'] >= min_pages]
            except ValueError:
                sg.popup('Ошибка', 'В фильтре страниц должно быть число!')
                continue

        # Обновление таблицы с фильтрацией
        window['-TABLE-'].update(
            values=[[b['title'], b['author'], b['genre'], b['pages']] for b in filtered_books]
        )

    elif event == 'Сохранить':
        save_books(books)
        sg.popup('Успех', 'Данные сохранены в books.json и закоммичены в Git!')

    elif event == 'Загрузить':
        books = load_books()
        window['-TABLE-'].update(
            values=[[b['title'], b['author'], b['genre'], b['pages']] for b in books]
        )
        sg.popup('Успех', 'Данные загружены из books.json!')

# Закрытие окна
window.close()
