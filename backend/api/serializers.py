from django.db import transaction

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
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
        fields = ['avatar']


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username',  'first_name', 'last_name',
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
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False


class UserListSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes_count', 'recipes')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False

    def get_recipes_count(self, obj):
        return self.context.get('recipes_count',
                                Recipe.objects.filter(author=obj).count())

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = self.context.get('recipes', Recipe.objects.filter(author=obj))
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
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
    author = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def create(self, validated_data):
        user = validated_data.get('user')
        author = validated_data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')
        return Subscription.objects.create(user=user, author=author)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


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
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingCart.objects.filter(user=self.context['request'].user,
                                            recipe=obj).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'author', 'tags', 'ingredients',
                  'image', 'cooking_time')

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise serializers.ValidationError(f'{field} - '
                                                  f'Обязательное поле.')
        if not obj.get('tags'):
            raise serializers.ValidationError('Нужно указать минимум 1 тег.')
        tag_id_list = [tag.id for tag in obj.get('tags')]
        if len(tag_id_list) != len(set(tag_id_list)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно указать минимум 1 ингредиент.')
        ingredient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(ingredient_id_list)
        if len(ingredient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        for ingredient in obj.get('ingredients'):
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.')
        return obj

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredients_list = []
        for ingredient in ingredients:
            try:
                ingredient_instance = Ingredient.objects.get(
                    pk=ingredient['id'])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f"Ингредиент с id {ingredient['id']} не существует.")
            ingredients_list.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_instance,
                amount=ingredient['amount']
            ))
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
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
