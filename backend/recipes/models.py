from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils.crypto import get_random_string

from .constants import (MAX_LENGTH_INGREDIENT, MAX_LENGTH_MEASURE,
                        MAX_LENGTH_RECIPE, MAX_LENGTH_TAG, MAX_LENGTH_URL,
                        TITLE_CUT)

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField('Название',
                            max_length=MAX_LENGTH_INGREDIENT,
                            unique=True)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=MAX_LENGTH_MEASURE)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name[:TITLE_CUT]


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField('Название',
                            max_length=MAX_LENGTH_TAG,
                            unique=True)
    slug = models.SlugField('Идентификатор',
                            max_length=MAX_LENGTH_TAG,
                            unique=True,
                            validators=[
                                RegexValidator(
                                    regex=r'^[-a-zA-Z0-9_]+$',
                                    message='Недопустимые символы в названии.')
                            ])

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:TITLE_CUT]


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор публикации',
                               related_name='recipes')
    name = models.CharField('Название',
                            max_length=MAX_LENGTH_RECIPE)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientInRecipe',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag,
                                  verbose_name='Теги')
    image = models.ImageField('Изображение',
                              upload_to='recipes/')
    short_url = models.CharField('Короткий URL',
                                 max_length=MAX_LENGTH_URL,
                                 unique=True,
                                 blank=True)

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = get_random_string(8)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:TITLE_CUT]


class IngredientInRecipe(models.Model):
    """Модель ингредиента в рецепте."""

    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингредиент',
                                   related_name='recipe_ingredients')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='recipe_ingredients')
    amount = models.PositiveSmallIntegerField('Количество')

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='ingredient_recipe_unique')]

    def __str__(self):
        return f'{self.recipe} включает {self.amount} {self.ingredient}'


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='favorites',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='favorited_by',
                               verbose_name='Рецепты в избранном')

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_user_favorite')
        ]
        ordering = ('user',)

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='shopping_cart',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='in_shopping_cart',
                               verbose_name='Рецепты в списке покупок')

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart')
        ]
        ordering = ('user',)

    def __str__(self):
        return f'Список покупок {self.user}: {self.recipe}'
