from django.db import transaction

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.constants import MIN_INGREDIENT_AMOUNT
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError('Вы не добавили аватар.')
        return value


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}


class UserDetailSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and request.user.subscriptions.filter(author=obj).exists())


class UserListSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar')


class UserSerializer(UserDetailSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserDetailSerializer.Meta):
        model = User
        fields = UserDetailSerializer.Meta.fields + ('recipes_count',
                                                     'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True,
                                        context=self.context).data

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Введен неверный пароль.')
        return value

    def validate_new_password(self, value):
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                              required=True)
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
                                                required=True)

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Подписка уже существует.')
        return data

    def to_representation(self, instance):
        representation = UserSerializer(instance.author,
                                        context=self.context).data
        recipes_limit = (self.context['request']
                         .query_params.get('recipes_limit'))

        if recipes_limit and recipes_limit.isdigit():
            representation['recipes'] = representation['recipes'][:int(
                recipes_limit)]
        representation['is_subscribed'] = True
        return representation


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                f'Количество ингредиента должно быть больше '
                f'{MIN_INGREDIENT_AMOUNT}.')
        return value


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(source='recipe_ingredients',
                                               many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'author', 'tags', 'ingredients',
                  'image', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.shopping_carts.filter(user=request.user).exists())


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'author', 'tags', 'ingredients',
                  'image', 'cooking_time')

    def validate(self, obj):
        if not self.instance and 'image' not in self.initial_data:
            raise serializers.ValidationError('Обязательное поле.')
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError('Обязательное поле.')
        tags = obj.get('tags')
        if not tags:
            raise serializers.ValidationError('Нужно указать минимум 1 тег.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        ingredients = obj.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.')
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        return obj

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        if self.instance:
            recipe.recipe_ingredients.all().delete()
        recipe.tags.set(tags)
        ingredients_list = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if 'image' not in validated_data:
            validated_data.pop('image', None)
        instance = super().update(instance, validated_data)
        self.tags_and_ingredients_set(instance, tags, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe', 'user')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe,
                                        context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe,
                                        context=self.context).data
