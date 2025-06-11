from rest_framework import serializers
from djoser.serializers import UserSerializer as BaseUserSerializer
from users.models import User, Follow
from recipes.models import Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingCart
from drf_extra_fields.fields import Base64ImageField
from django.db import IntegrityError
import re

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MIN_AMOUNT = 1


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "username": {"required": True, "allow_blank": False},
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "password": {"write_only": True, "required": True},
        }

    def to_internal_value(self, data):
        email = data.get("email")
        username = data.get("username")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        if not email or email.strip() == "":
            raise serializers.ValidationError(
                {"email": "Это поле не может быть пустым."}
            )
        if len(email) > 254:
            raise serializers.ValidationError(
                {"email": "Максимальная длина email 254 символа."}
            )
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "Пользователь с таким email уже существует."}
            )

        if not username or username.strip() == "":
            raise serializers.ValidationError(
                {"username": "Это поле не может быть пустым."}
            )
        if len(username) > 150:
            raise serializers.ValidationError(
                {"username": "Максимальная длина имени пользователя 150 символов."}
            )
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {"username": "Пользователь с таким именем уже существует."}
            )
        if not re.match(r"^[\w.@+-]+\Z", username):
            raise serializers.ValidationError(
                {"username": "Имя пользователя содержит недопустимые символы."}
            )

        if not first_name or first_name.strip() == "":
            raise serializers.ValidationError(
                {"first_name": "Это поле не может быть пустым."}
            )
        if len(first_name) > 150:
            raise serializers.ValidationError(
                {"first_name": "Максимальная длина имени 150 символов."}
            )

        if not last_name or last_name.strip() == "":
            raise serializers.ValidationError(
                {"last_name": "Это поле не может быть пустым."}
            )
        if len(last_name) > 150:
            raise serializers.ValidationError(
                {"last_name": "Максимальная длина фамилии 150 символов."}
            )

        validated_data = super().to_internal_value(data)
        validated_data["email"] = email
        validated_data["username"] = username
        validated_data["first_name"] = first_name
        validated_data["last_name"] = last_name
        return validated_data

    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError("Максимальная длина email 254 символа.")
        return value

    def validate_username(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Максимальная длина имени пользователя 150 символов."
            )
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise serializers.ValidationError(
                "Имя пользователя содержит недопустимые символы."
            )
        return value

    def validate_first_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError("Максимальная длина имени 150 символов.")
        return value

    def validate_last_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Максимальная длина фамилии 150 символов."
            )
        return value

    def create(self, validated_data):
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except IntegrityError:
            raise serializers.ValidationError(
                {"detail": "Пользователь с таким email или именем уже существует."}
            )

    def to_representation(self, instance):
        request = self.context.get("request")
        if request and request.method == "POST":
            return {
                "id": instance.id,
                "email": instance.email,
                "username": instance.username,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
            }
        avatar_url = None
        if instance.avatar and hasattr(instance.avatar, "url") and request:
            avatar_url = request.build_absolute_uri(instance.avatar.url)
        return {
            "id": instance.id,
            "email": instance.email,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "avatar": avatar_url,
            "is_subscribed": (
                request.user.following.filter(following=instance).exists()
                if request and request.user.is_authenticated
                else False
            ),
        }


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    def validate(self, data):
        if data["amount"] < MIN_AMOUNT:
            raise serializers.ValidationError(
                {"amount": "Количество ингредиента должно быть не менее 1."}
            )
        return data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source="recipeingredient_set"
    )
    ingredients_input = IngredientAmountSerializer(
        many=True, write_only=True, required=True
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME, required=True
    )
    name = serializers.CharField(max_length=200, required=True)
    text = serializers.CharField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "text",
            "ingredients",
            "ingredients_input",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def to_internal_value(self, data):
        if "ingredients" in data and "ingredients_input" not in data:
            data = data.copy()
            data["ingredients_input"] = data.pop("ingredients")
        return super().to_internal_value(data)

    def validate(self, data):
        request = self.context["request"]
        ingredients_data = data.get("ingredients_input", [])

        if not ingredients_data:
            raise serializers.ValidationError(
                {"ingredients": "Список ингредиентов не может быть пустым."}
            )

        ingredient_ids = [item["id"] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        if request and request.method in ["POST", "PATCH"]:
            name = data.get("name")
            if name and Recipe.objects.filter(name=name, author=request.user).exists():
                if request.method == "POST" or (
                    request.method == "PATCH"
                    and not self.instance
                    or not Recipe.objects.filter(
                        id=self.instance.id, name=name, author=request.user
                    ).exists()
                ):
                    raise serializers.ValidationError(
                        {
                            "name": "Рецепт с таким названием уже существует у этого автора."
                        }
                    )

        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Изображение обязательно для заполнения.")
        return value

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Название рецепта не может быть пустым.")
        if len(value) > 200:
            raise serializers.ValidationError(
                "Название рецепта не может превышать 200 символов."
            )
        return value

    def validate_text(self, value):
        if not value:
            raise serializers.ValidationError("Описание рецепта не может быть пустым.")
        return value

    def validate_cooking_time(self, value):
        if value is None:
            raise serializers.ValidationError("Время приготовления обязательно.")
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                "Время приготовления должно быть не менее 1 минуты."
            )
        if value > MAX_COOKING_TIME:
            raise serializers.ValidationError(
                f"Время приготовления не может превышать {MAX_COOKING_TIME} минут."
            )
        return value

    def _update_ingredients(self, recipe, ingredients_data):
        if ingredients_data:
            recipe.recipeingredient_set.all().delete()
            recipe_ingredients = []
            for ingredient_data in ingredients_data:
                try:
                    ingredient = Ingredient.objects.get(id=ingredient_data["id"])
                except Ingredient.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "ingredients": f"Ингредиент с ID {ingredient_data['id']} не существует."
                        }
                    )
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=ingredient_data["amount"],
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients_input")
        recipe = Recipe.objects.create(**validated_data)
        self._update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients_input", None)
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.save()
        if ingredients_data is not None:
            self._update_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        author_data = data["author"]
        author_data["is_subscribed"] = (
            request.user.following.filter(following=instance.author).exists()
            if request and request.user.is_authenticated
            else False
        )
        avatar_url = None
        if (
            instance.author.avatar
            and hasattr(instance.author.avatar, "url")
            and request
        ):
            avatar_url = request.build_absolute_uri(instance.author.avatar.url)
        author_data["avatar"] = avatar_url
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        data["ingredients"] = RecipeIngredientSerializer(ingredients, many=True).data
        return data

    def get_is_favorited(self, obj):
        request = self.context["request"]
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(recipe=obj).exists()
        return False

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
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit", 3)
        recipes = obj.following.recipes.all()[: int(recipes_limit)]
        return ShortRecipeSerializer(
            recipes, many=True, context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        following_data = data.pop("following")
        result = {
            "id": following_data["id"],
            "email": following_data["email"],
            "username": following_data["username"],
            "first_name": following_data["first_name"],
            "last_name": following_data["last_name"],
            "is_subscribed": following_data.get("is_subscribed", False),
            "avatar": following_data.get("avatar", None),
            "recipes": data["recipes"],
            "recipes_count": data["recipes_count"],
        }
        return result


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate(self, data):
        if not data.get("avatar"):
            raise serializers.ValidationError(
                {"avatar": "Изображение обязательно для заполнения."}
            )
        return data
