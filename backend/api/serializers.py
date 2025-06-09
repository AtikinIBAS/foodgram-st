from rest_framework import serializers
from djoser.serializers import UserSerializer as BaseUserSerializer
from users.models import User, Follow
from recipes.models import Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingCart
from drf_extra_fields.fields import Base64ImageField

# Константы для валидации cooking_time
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000

class UserSerializer(BaseUserSerializer):
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_in_cart = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "password",
            "recipes_in_cart",
        )
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "username": {"required": True, "allow_blank": False},
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "password": {"write_only": True, "required": True},
        }

    def to_internal_value(self, data):
        email = data.get('email')
        if not email:
            raise serializers.ValidationError({'email': 'Это поле обязательно.'})
        validated_data = super().to_internal_value(data)
        validated_data['email'] = email
        return validated_data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_is_subscribed(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated:
            return request.user.following.filter(following=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context["request"]
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_recipes_in_cart(self, obj):
        return obj.shopping_carts.count()

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")

class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")

class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients_display = RecipeIngredientSerializer(
        source="recipeingredient_set", many=True, read_only=True
    )
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    authorId = serializers.ReadOnlyField(source='author.id')
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "text",
            "ingredients",
            "ingredients_display",
            "cooking_time",
            "is_favorited",
            "authorId",
            'is_in_shopping_cart',
        )

    def validate(self, data):
        request = self.context["request"]
        if request and request.method == "POST":
            name = data.get("name")
            if Recipe.objects.filter(name=name, author=request.user).exists():
                raise serializers.ValidationError(
                    {"name": "Рецепт с таким названием уже существует у этого автора."}
                )
        return data

    def _update_ingredients(self, recipe, ingredients_data):
        if ingredients_data:
            recipe.recipeingredient_set.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(id=ingredient_data["id"]),
                    amount=ingredient_data["amount"]
                )
                for ingredient_data in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get("cooking_time", instance.cooking_time)
        instance.save()
        if ingredients_data is not None:
            self._update_ingredients(instance, ingredients_data)
        return instance

    def get_is_favorited(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(recipe=obj).exists()
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["ingredients"] = data.pop("ingredients_display", [])
        return data

    def get_is_in_shopping_cart(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated:
            return request.user.shopping_carts.filter(recipe=obj).exists()
        return False

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")

class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")

class FollowSerializer(serializers.ModelSerializer):
    following = UserSerializer(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ("following", "recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context["request"]
        recipes_limit = request.query_params.get("recipes_limit", 3)
        recipes = obj.following.recipes.all()[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True, context={"request": request}).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        following_data = data.pop('following')
        data.update(following_data)
        return data

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)