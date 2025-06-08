# Foodgram - "Форум кулинаров"

## Описание

Foodgram — это веб-приложение, в котором пользователи могут публиковать рецепты, добавлять рецепты в избранное, список покупок, а также подписываться на других пользователей. Проект позволяет формировать список покупок на основе добавленных рецептов и выгружать его в формате `.txt`.

## Технологии

* Python 3.10
* Django 4.2
* Django REST Framework
* PostgreSQL 17
* Gunicorn
* Nginx
* Docker / Docker Compose
* GitHub Actions

## Установка и запуск проекта локально с нуля

### 1. Клонировать репозиторий

```bash
git clone https://github.com/AtikinIBAS/foodgram-st.git
cd foodgram-st
```

### 2. Создать и настроить файл окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`, заполнив:

* `SECRET_KEY` — уникальный секретный ключ Django
* `POSTGRES_*` — параметры подключения к базе данных

### 3. Запуск проекта в Docker

```bash
cd infra
sudo docker compose up --build
```

Проект будет доступен по адресу: [http://localhost](http://localhost)

### 4. Выполнить миграции и создать суперпользователя, загрузить ингридиенты в базу

```bash
sudo docker compose exec backend python mange.py makemigrations
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py createsuperuser
sudo docker compose exec backend python manage.py load_ingredients
```

### 5. Собрать статику

```bash
sudo docker compose exec backend python manage.py collectstatic --no-input
```


## Документация API

Документация доступна по адресу:

```
http://localhost/api/docs/
```

## Примеры работы

Страница рецепта
![alt text](/readme_media/recipe_page.png)

Страница всех рецептов форума
![alt text](/readme_media/recipes_page.png)

Страница корзины покупок
![alt text](/readme_media/shopping_cart.png)