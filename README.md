
# Welcome to [alxlen.ru](http://alxlen.ru)
## Проект Foodgram.

### Запуск в контейнерах и CI/CD с помощью GitHub Actions

![CI/CD Status](https://github.com/alxlen/foodgram/actions/workflows/main.yml/badge.svg)

### Описание.

Представляю вам проект, созданный во время обучения в Яндекс Практикуме.  
Этот проект — часть учебного курса, но он создан полностью самостоятельно.

Цель этого сайта — дать возможность пользователям создавать и хранить рецепты на  
онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для  
приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в  
список избранных.

Чтобы использовать все возможности сайта — нужна регистрация.  
Проверка адреса электронной почты не осуществляется, вы можете ввести любой email.

### Технологии.

- Python 3.9
- Django 3.2
- Django REST Framework 3.12
- PostgreSQL
- Docker
- Nginx

### Развертывание проекта.

1. **Подготовка сервера для деплоя:**
   - Настройте сервер, установите необходимые пакеты безопасности.
   - Настройте SSH-доступ.

2. **Установка Docker и Docker Compose:**
   - Установите Docker:
     ```bash
     sudo apt update
     sudo apt install docker.io
     ```
   - Установите Docker Compose:
     ```bash
     sudo apt install docker-compose
     ```

3. **Настройка доменного имени и SSL:**
   - Настройте DNS для вашего домена.
   - Установите SSL сертификат (например, с помощью Certbot).

4. **Клонирование репозитория и настройка переменных окружения:**
   - Клонируйте репозиторий на сервер:
     ```bash
     git clone https://github.com/ваш-репозиторий/foodgram.git
     cd foodgram
     ```
   - Создайте файл `.env` в корневом каталоге проекта на основе примера `.env.example`.

5. **Настройка GitHub Actions:**
   - Добавьте в репозиторий GitHub следующие секреты:
     - `DOCKER_USERNAME`: Ваше имя пользователя на DockerHub.
     - `DOCKER_PASSWORD`: Ваш пароль на DockerHub.
     - `HOST`: Адрес вашего сервера для деплоя.
     - `USER`: Имя пользователя для подключения по SSH.
     - `SSH_KEY`: Приватный SSH-ключ для подключения к серверу.
     - `SH_PASSPHRASE`: Пароль от SSH-ключа.
     - `TELEGRAM_TO`: Идентификатор чата Telegram для уведомлений.
     - `TELEGRAM_TOKEN`: Токен вашего Telegram-бота.

6. **Развертывание проекта:**
   - Сделайте push в ветку `main` вашего репозитория.
   - GitHub Actions автоматически запустит workflow:
     - Протестирует backend и frontend.
     - Соберет Docker образы и отправит их в DockerHub.
     - Задеплоит проект на ваш сервер с помощью SSH и Docker Compose.
     - Отправит уведомление в Telegram об успешном деплое.

7. **Запуск проекта локально с использованием Docker Compose:**
   - Перейдите в каталог проекта и выполните команду:
     ```bash
     docker-compose up -d
     ```
   - Проект будет доступен по адресу: `http://localhost`.

8. **Наполнение базы данных:**
   - В проекте предусмотрен скрипт для наполнения базы данных ингредиентами.  
   - Чтобы им воспользоваться, выполните следующие команды:
     ```bash
     python manage.py import_ingredients
     ```

## Документация API

Документация API доступна по адресу: [alxlen.ru/api/docs/](http://alxlen.ru/api/docs/)

### Автор.

Александр Ленко.
