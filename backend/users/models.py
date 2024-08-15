from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from users.constants import (INVALID_USERNAME, MAX_LENGTH_EMAIL,
                             MAX_LENGTH_FIRST_NAME, MAX_LENGTH_LAST_NAME,
                             MAX_LENGTH_USERNAME, USERNAME_VALIDATOR)


class User(AbstractUser):
    """Модель пользователя."""

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    email = models.EmailField('Электронная почта',
                              max_length=MAX_LENGTH_EMAIL,
                              unique=True)
    username = models.CharField('Имя пользователя',
                                max_length=MAX_LENGTH_USERNAME,
                                unique=True,
                                validators=[RegexValidator(
                                    regex=USERNAME_VALIDATOR,
                                    message='Недопустимые символы в имени.')])
    first_name = models.CharField('Имя',
                                  max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField('Фамилия',
                                 max_length=MAX_LENGTH_LAST_NAME)
    avatar = models.ImageField('Аватар',
                               upload_to='avatars/',
                               null=True, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    def clean(self):
        if self.username == INVALID_USERNAME:
            raise ValidationError('Недопустимое имя пользователя.')
        super().clean()


class Subscription(models.Model):
    """Модель подписки пользователей."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='subscriptions',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='subscribers',
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
