from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingList, Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели тегов."""
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "color",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингридиентов."""
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        """Метод обработки параметра is_subscribed."""
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Follow.objects.filter(user=user, author=obj).exists()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        queryset = (
            Recipe.objects.filter(author=obj.author).order_by("-pub_date"))
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор списка рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов в рецепте"""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(required=True)
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            'name',
            'measurement_unit',
            "amount",
        )

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Проверьте что количество ингредиентов больше 1!'
            )
        return value

    def get_measurement_unit(self, ingredient):
        measurement_unit = ingredient.ingredient.measurement_unit
        return measurement_unit

    def get_name(self, ingredient):
        name = ingredient.ingredient.name
        return name


class RecipesReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов (просмотр)."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_user(self):
        return self.context["request"].user

    def get_is_favorited(self, obj):
        """Проверяет находится ли рецепт в избранном."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favourite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет находится ли рецепт в продуктовой корзине."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(recipe=obj,
                                           user=request.user).exists()


class RecipesWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов (создание)."""
    author = CustomUserSerializer(read_only=True, required=False)
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get("ingredients")
        if not ingredients:
            raise ValidationError("Нужно выбрать минимум 1 ингредиент!")
        for ingredient in ingredients:
            try:
                int(ingredient.get("amount"))
                if int(ingredient.get("amount")) <= 0:
                    raise ValidationError(
                        "Количество должно быть положительным!")
            except Exception:
                raise ValidationError(
                    {"amount": "Колличество должно" "быть числом"})
            check_id = ingredient["id"]
            check_ingredient = Ingredient.objects.filter(id=check_id)
            if not check_ingredient.exists():
                raise serializers.ValidationError(
                    "Данного продукта нет в базе!")
        return data

    def validate_cooking_time(self, data):
        """Валидатор времени приготовления."""
        cooking_time = self.initial_data.get("cooking_time")
        try:
            int(cooking_time)
            if int(cooking_time) < 1:
                raise serializers.ValidationError(
                    "Время приготовления не может быть меньше 1!"
                )
            if int(cooking_time) > 720:
                raise serializers.ValidationError(
                    "Время приготовления не может быть больше 720!"
                )
        except Exception:
            raise ValidationError(
                {"cooking_time": "Время должно быть больше 0!"})
        return data

    def validate_tags(self, data):
        """Валидатор тегов."""
        tags = self.initial_data.get("tags")
        if not tags:
            raise ValidationError("Рецепт не может быть без тегов")
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f"Тег с id = {tag_id} не существует")
        tags_bd = set(tags)
        if len(tags) != len(tags_bd):
            raise ValidationError("Теги должны быть уникальными")
        return data

    def create_amount_ingredients(self, ingredients, recipe):
        """Создание ингредиентов в рецепте."""
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient.objects.filter(id=ingredient['id'])[:1]
            )
            ing, _ = IngredientInRecipe.objects.get_or_create(
                ingredient=current_ingredient,
                amount=ingredient["amount"],
            )
            recipe.ingredients.add(ing.id)

    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.set(tags)
        self.create_amount_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        if "ingredients" in validated_data:
            ingredients = validated_data.pop("ingredients")
            recipe.ingredients.clear()
            self.create_amount_ingredients(ingredients, recipe)
        if "tags" in validated_data:
            tags_data = validated_data.pop("tags")
            recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        serializer = RecipesReadSerializer(recipe, context=self.context)
        return serializer.data


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    id = serializers.CharField(
        read_only=True,
        source="recipe.id",
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source="recipe.cooking_time",
    )
    image = serializers.CharField(
        read_only=True,
        source="recipe.image",
    )
    name = serializers.CharField(
        read_only=True,
        source="recipe.name",
    )

    def validate(self, data):
        """Валидатор избранных рецептов"""
        recipe = data["recipe"]
        user = data["user"]
        if user == recipe.author:
            raise serializers.ValidationError(
                "Вы не можете добавить свои рецепты в избранное"
            )
        if Favourite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                "Вы уже добавили рецепт в избранное")
        return data

    def create(self, validated_data):
        """Метод создания избранного"""
        favorite = Favourite.objects.create(**validated_data)
        favorite.save()
        return favorite

    class Meta:
        model = Favourite
        fields = ("id", "name", "image", "cooking_time")


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор продуктовой корзины."""
    id = serializers.CharField(
        read_only=True,
        source="recipe.id",
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source="recipe.cooking_time",
    )
    image = serializers.CharField(
        read_only=True,
        source="recipe.image",
    )
    name = serializers.CharField(
        read_only=True,
        source="recipe.name",
    )

    class Meta:
        model = ShoppingList
        fields = ("id", "name", "image", "cooking_time")
