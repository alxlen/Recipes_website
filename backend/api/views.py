from django.db.models import Count, Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination, UserPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, PasswordChangeSerializer,
                          RecipeMinifiedSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscriptionSerializer,
                          TagSerializer, UserAvatarSerializer,
                          UserCreateSerializer, UserDetailSerializer,
                          UserListSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'me']:
            self.permission_classes = [AllowAny]
        elif self.action in ['avatar', 'set_password', 'subscribe',
                             'subscriptions']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'avatar':
            return UserAvatarSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action == 'me':
            return UserDetailSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'set_password':
            return PasswordChangeSerializer
        elif self.action in ['subscribe', 'subscriptions']:
            return SubscriptionSerializer
        return UserSerializer

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response({'detail': 'Вы не добавили аватар.'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = UserAvatarSerializer(user, data=request.data,
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Незарегистрированный пользователь.'},
                status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data,
                                              context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Пароль изменен.'},
                            status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response({'detail': 'Подписка уже существует.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            recipes_limit = request.query_params.get('recipes_limit')
            recipes_query = Recipe.objects.filter(author=author)
            if recipes_limit:
                recipes_query = recipes_query[:int(recipes_limit)]
            recipes_count = Recipe.objects.filter(author=author).count()
            serializer = UserSerializer(
                author, context={'request': request, 'recipes': recipes_query,
                                 'recipes_count': recipes_count}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Подписка не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = self.request.user
        authors_id = user.subscriber.values('author')
        authors = User.objects.filter(id__in=authors_id).annotate(
            recipes_count=Count('recipes')
        ).prefetch_related(
            Prefetch('recipes', queryset=Recipe.objects.all())
        )
        paginated_queryset = self.paginate_queryset(authors)
        serializer = UserSerializer(paginated_queryset, many=True,
                                    context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        recipe_id = kwargs['pk']
        user = request.user

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=recipe_id)
            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                Favorite.objects.create(user=user, recipe=recipe)
                serializer = RecipeMinifiedSerializer(
                    recipe, context={"request": request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if not Recipe.objects.filter(id=recipe_id).exists():
                return Response({'errors': 'Рецепт не найден.'},
                                status=status.HTTP_404_NOT_FOUND)
            favorite_item = Favorite.objects.filter(
                user=user, recipe_id=recipe_id).first()
            if not favorite_item:
                return Response({'errors': 'Рецепт не найден в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            favorite_item.delete()
            return Response({'detail': 'Рецепт удален из избранного.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({'short-link': recipe.short_url},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe_id = kwargs['pk']
        user = request.user

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=recipe_id)
            if not ShoppingCart.objects.filter(
                    user=user, recipe=recipe).exists():
                ShoppingCart.objects.create(user=user, recipe=recipe)
                serializer = RecipeMinifiedSerializer(
                    recipe, context={"request": request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if not Recipe.objects.filter(id=recipe_id).exists():
                return Response({'errors': 'Рецепт не найден.'},
                                status=status.HTTP_404_NOT_FOUND)
            shopping_cart_item = ShoppingCart.objects.filter(
                user=user, recipe_id=recipe_id).first()
            if not shopping_cart_item:
                return Response(
                    {'errors': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST)
            shopping_cart_item.delete()
            return Response({'detail': 'Рецепт удален из списка покупок.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = (ShoppingCart.objects.filter(user=user)
                               .select_related('recipe'))
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in=shopping_cart_items.values('recipe')).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            total_quantity=Sum('amount'))
        content_type = 'text/plain'
        response = HttpResponse(content_type=content_type)
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_cart.txt"')
        for ingredient in ingredients:
            response.write(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_quantity']}\n")
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [IngredientFilter]
    search_fields = ['^name']
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]
