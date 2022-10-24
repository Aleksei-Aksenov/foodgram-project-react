# :bread: FoodGram продуктовый помощник

## Описание:

На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в  Избранное, а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления выбранных блюд.

#### Приложение работает на следующих технологиях:

<img src="https://img.shields.io/badge/django-blue?style=for-the-badge&logo=django&logoColor=white"/> <img src="https://img.shields.io/badge/rest-framework-blue?style=for-the-badge&logo=django&logoColor=white"/> <img src="https://img.shields.io/badge/postgres-blue?style=for-the-badge&logo=PostgreSQL&logoColor=white"/> <img src="https://img.shields.io/badge/react-blue?style=for-the-badge&logo=React&logoColor=white"/>

Проект размещен по адресу:
    [62.84.113.243](http://62.84.113.243/)
    
Аккаунт для проверки админ-панели:

        Адрес: http://62.84.113.243/admin/
        Эл. почта: admin@gmail.com
        Логин: admin
        Пароль: 123Admin

#### :pencil2: Авторы проекта:
- backend (Алексей Аксёнов)
- frontend (Yandex.Practicum)

#### Запуск проекта в dev-режиме:

1. Клонировать репозиторий и перейти в него в командной строке:

        git clone https://github.com/Aleksei-Aksenov/foodgram-project-react
        cd foodgram-project-react

2. Cоздать и активировать виртуальное окружение:

        # - Если у вас linux/MacOS:
        python3 -m venv venv
        source venv/bin/activate

        # - Если у вас Windows:
        python -m venv venv
        source venv/Scripts/activate
        
3. Установить зависимости из файла requirements.txt:

        python3 -m pip install --upgrade pip
        pip install -r requirements.txt

4. Выполнить миграции:

        python3 manage.py migrate

5. Запустить проект:

        python3 manage.py runserver


#### Запуск проекта с помощью CI/CD

1. Подключиться к серверу и выполнить команды по установке Docker и Docker Compose:

        sudo apt update && sudo apt upgrade -y && sudo apt install curl -y
        sudo curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo rm get-docker.sh
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose

2. Перенести файлы docker-compose.yml и default.conf на сервер (терминал открыт в папке проекта infra)
        
        scp docker-compose.yml username@server_ip:/home/username/
        scp default.conf username@server_ip:/home/username/
        
3. Заполнить файл .env.  (либо воспользоваться подсказкой из файла .env.example, переименовав его в .env)

        DB_ENGINE=django.db.backends.postgresql
        DB_NAME= # название БД
        POSTGRES_USER= # ваше имя пользователя
        POSTGRES_PASSWORD= # пароль для доступа к БД
        DB_HOST=db
        DB_PORT=5432
        SECRET_KEY= # секретный ключ Django
        
4. Выполнить стартовые команды в контейнере backend.

        sudo docker-compose exec backend python manage.py makemigrations
        sudo docker-compose exec backend python manage.py migrate
        sudo docker-compose exec backend python manage.py createsuperuser
        sudo docker-compose exec backend python manage.py collectstatic --no-input
        
5. Загрузить теги и ингредиенты

        sudo docker-compose exec backend python manage.py load_tags
        sudo docker-compose exec backend python manage.py load_ingredients
        
#### Запуск проекта через Docker

1. В папке проекта infra выполнить команду:

        sudo docker-compose up -d

2. После успешной сборки, выполнить миграции в контейнере backend.

        sudo docker-compose exec backend python manage.py makemigrations
        sudo docker-compose exec backend python manage.py migrate --noinput
        
3. Создать суперпользователя.

        sudo docker-compose exec backend python manage.py createsuperuser
        
4. Загрузить статику.

        sudo docker-compose exec backend python manage.py collectstatic --no-input
        
5. Загрузить теги и ингредиенты.

        sudo docker-compose exec backend python manage.py load_tags
        sudo docker-compose exec backend python manage.py load_ingredients

