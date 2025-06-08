from django.contrib import admin
from recipes.models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)

class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "get_favorites_count", "show_ingredient_count")
    search_fields = ("name", "author__username")
    readonly_fields = ("get_favorites_count",)
    inlines = [RecipeIngredientInline]

    def get_favorites_count(self, obj):
        return len(obj.favorite_set.all())
    get_favorites_count.short_description = "В избранном"

    def show_ingredient_count(self, obj):
        return obj.ingredients.count()
    show_ingredient_count.short_description = "Число ингредиентов"

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")

#@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_recipe']

    def get_user(self, obj):
        return obj.user.username
    get_user.short_description = 'Пользователь'

    def get_recipe(self, obj):
        return obj.recipe.name
    get_recipe.short_description = 'Рецепт'

admin.site.register(ShoppingCart, ShoppingCartAdmin)