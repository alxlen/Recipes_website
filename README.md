
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

- Подготовьте свой сервер для деплоя
- Произведите настройки безопасности и SSH-доступа
- Установите Docker и Docker Compose
- Произведите настройки DNS и доменного имени
- Настройте SSL
- Клонируйте репозиторий на GitHub
- Настройте переменные окружения (см. пример .env.example)
- Добавьте в репозиторий GitHub следующие секреты:
DOCKER_USERNAME: Ваше имя пользователя на DockerHub  
DOCKER_PASSWORD: Ваш пароль на DockerHub  
HOST: Адрес вашего сервера для деплоя  
USER: Имя пользователя для подключения по SSH  
SSH_KEY: Приватный SSH-ключ для подключения к серверу  
SH_PASSPHRASE: Пароль от SSH-ключа  
TELEGRAM_TO: Идентификатор чата Telegram, куда будет отправлено уведомление  
TELEGRAM_TOKEN: Токен вашего Telegram-бота  
- Сделайте пуш/пулл в ветку main вашего репозитория. 
- GitHub Actions автоматически запустит workflow:  
Протестирует backend и frontend;  
Соберет Docker образы и отправит их в DockerHub;    
Задеплоит проект на ваш сервер с помощью SSH и Docker Compose;  
Отправит уведомление в Telegram о успешном деплое.  

### Автор.

Александр Ленко.
