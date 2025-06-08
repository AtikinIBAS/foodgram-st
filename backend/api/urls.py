from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import AccountViewSet, RecipeViewSet, IngredientViewSet, ShoppingCartIngredientsView, redirect_short_link

router = DefaultRouter()
router.register("users", AccountViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include('djoser.urls')),
    path("auth/", include('djoser.urls.authtoken')),
    path("shopping_cart/ingredients/", ShoppingCartIngredientsView.as_view(), name='shopping_cart_ingredients'),
    path("s/<uuid:slug>/", redirect_short_link, name='short-link'),
]
