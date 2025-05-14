# Django Shop

Полнофункциональный интернет-магазин, разработанный на Django.

## Возможности

- Регистрация и вход пользователей
- Каталог товаров с фильтрацией по категориям
- Просмотр подробностей товара
- Добавление товаров в корзину
- Оформление заказов
- Админка для управления товарами, заказами и пользователями
- REST API

## Установка

1. Клонировать репозиторий:
git clone https://github.com/yourname/django_shop.git
cd django_shop

2. Создать виртуальное окружение:
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows

3.Установить зависимости:
pip install -r requirements.txt

4.Настроить файл .env.

5.Применить миграции и загрузить фикстуры:
python manage.py migrate
python manage.py loaddata fixtures.json

6.Запустить сервер:
python manage.py runserver
