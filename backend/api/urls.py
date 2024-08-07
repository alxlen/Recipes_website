from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/avatar/',
         UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
         name='avatar'),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
    path('recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_link'}), name='recipes-get-link'),
]
