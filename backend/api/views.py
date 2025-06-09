from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer,
    RecipeSerializer,
    IngredientSerializer,
    FollowSerializer,
    AvatarSerializer,
    RecipeIngredientSerializer,
)
from users.models import User, Follow
from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart
from rest_framework.views import APIView
from recipes.models import RecipeIngredient
from .permissions import IsAuthorOrReadOnly
from .pagination import LimitPageNumberPagination
from django.urls import reverse
from django.shortcuts import redirect
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash


class AccountViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = LimitPageNumberPagination

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.following.filter(following=author).exists():
            return Response(
                {"detail": "Уже подписан"}, status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.create(follower=user, following=author)
        serializer = UserSerializer(author, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        follow = user.following.filter(following=author).first()
        if not follow:
            return Response(
                {"detail": "Вы не подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        follows = user.following.all()
        paginator = LimitPageNumberPagination()
        paginator.page_size = 6
        result_page = paginator.paginate_queryset(follows, request)
        serializer = FollowSerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        permission_classes=[permissions.IsAuthenticated],
    )
    def update_avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"detail": "Необходимо указать current_password и new_password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"detail": "Неверный текущий пароль."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(
            {"detail": "Пароль успешно изменён."}, status=status.HTTP_200_OK
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "author__username"]
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        author_id = self.request.query_params.get("author", None)

        if author_id:
            queryset = queryset.filter(author_id=author_id)

        if user.is_authenticated:
            is_favorited = self.request.query_params.get("is_favorited", None)
            is_in_shopping_cart = self.request.query_params.get(
                "is_in_shopping_cart", None
            )

            if is_favorited == "1":
                queryset = queryset.filter(favorite__user=user).distinct()
            if is_in_shopping_cart == "1":
                queryset = queryset.filter(in_shopping_carts__user=user).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == "POST":
            if user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {"detail": "Уже в избранном"}, status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            favorite = user.favorites.filter(recipe=recipe).first()
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Не в избранном"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if user.shopping_carts.filter(recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в корзине"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            shopping_cart = user.shopping_carts.filter(recipe=recipe).first()
            if shopping_cart:
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Рецепт не в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart_ingredients(self, request):
        user = request.user
        shopping_cart = user.shopping_carts.all()
        ingredients = Ingredient.objects.filter(
            recipe__in=shopping_cart.values("recipe")
        )
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.shopping_carts.all()
        recipes = [item.recipe for item in shopping_cart]
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )

        content = "Список покупок\n"
        for ingredient in ingredients:
            content += f"{ingredient['ingredient__name']} ({ingredient['ingredient__measurement_unit']}) — {ingredient['total_amount']}\n"
        return HttpResponse(
            content,
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="shopping_list.txt"'},
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = request.build_absolute_uri(
            reverse("short-link", args=[recipe.short_uuid])
        )
        return Response({"short_link": short_link})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by("id")
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get("name")
        if name:
            return self.queryset.filter(name__istartswith=name)
        return self.queryset


class ShoppingCartIngredientsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        shopping_cart = user.shopping_carts.all()
        recipes = [item.recipe for item in shopping_cart]
        ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
        serializer = RecipeIngredientSerializer(ingredients, many=True)
        return Response(serializer.data)


def redirect_short_link(request, slug):
    recipe = get_object_or_404(Recipe, short_uuid=slug)
    url = reverse("recipes-detail", args=[recipe.id])
    return redirect(url)
