from django.db import models
from users.models import User
import uuid

class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    measurement_unit = models.CharField(max_length=20, verbose_name="Единица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name

class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(upload_to='recipes/', verbose_name="Картинка")
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', verbose_name="Ингредиенты")
    cooking_time = models.PositiveIntegerField(verbose_name="Время приготовления (мин)")
    short_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-id"]

    def __str__(self):
        return self.name

    def count_ingredients(self):
        return self.ingredients.count()

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="unique_favorite")]

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт", related_name="shopping_carts")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="unique_shopping_cart")]