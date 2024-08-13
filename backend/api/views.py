from io import StringIO

from django.db.models import Count, Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import RecipePagination, UserPagination
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             PasswordChangeSerializer, RecipeReadSerializer,
                             RecipeWriteSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserAvatarSerializer, UserCreateSerializer,
                             UserDetailSerializer, UserListSerializer,
                             UserSerializer)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User


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
        elif self.action in ['me', 'retrieve']:
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
            serializer = UserAvatarSerializer(user, data=request.data,
                                              partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data,
                                              context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль изменен.'},
                        status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = self.request.user
        authors_id = user.subscriptions.values('author')
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def handle_post_action(request, serializer_class, user, recipe):
        serializer = serializer_class(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def handle_delete_action(model_class, user, recipe):
        obj = model_class.objects.filter(user=user, recipe=recipe).first()
        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Объект не найден.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return self.handle_post_action(request, FavoriteSerializer,
                                           user, recipe)
        return self.handle_delete_action(Favorite, user, recipe)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return self.handle_post_action(request, ShoppingCartSerializer,
                                           user, recipe)
        return self.handle_delete_action(ShoppingCart, user, recipe)

    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({'short-link': recipe.short_url},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = self.get_shopping_cart_ingredients(user)
        return self.create_shopping_cart_file(ingredients)

    def get_shopping_cart_ingredients(self, user):
        shopping_cart_items = (ShoppingCart.objects.filter(user=user)
                               .select_related('recipe'))
        return IngredientInRecipe.objects.filter(
            recipe__in=shopping_cart_items.values('recipe')
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

    def create_shopping_cart_file(self, ingredients):
        output = StringIO()
        for ingredient in ingredients:
            output.write(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_quantity']}\n"
            )
        output.seek(0)
        response = FileResponse(output, as_attachment=True,
                                content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_cart.txt"')
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
