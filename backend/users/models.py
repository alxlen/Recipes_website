from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                        MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField('Электронная почта',
                              max_length=MAX_LENGTH_EMAIL,
                              unique=True)
    username = models.CharField('Имя пользователя',
                                max_length=MAX_LENGTH_USERNAME,
                                unique=True,
                                validators=[RegexValidator(
                                    regex=r'^[\w.@+-]+$',
                                    message='Недопустимые символы в имени.')])
    first_name = models.CharField('Имя',
                                  max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField('Фамилия',
                                 max_length=MAX_LENGTH_LAST_NAME)
    avatar = models.ImageField('Аватар',
                               upload_to='avatars/',
                               null=True, blank=True)

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователей."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='subscriber',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='subscribed_to',
                               verbose_name='Подписки')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription')
        ]
        ordering = ('user',)

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
