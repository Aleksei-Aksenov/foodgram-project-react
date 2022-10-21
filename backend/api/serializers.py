from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favourite, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingList, Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "color",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit"
        )


class CustomUserSerializer(serializers.ModelSerializer):
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
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class FollowSerializer(serializers.ModelSerializer):
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
        queryset = Recipe.objects.filter(author=obj.author).order_by(
            "-pub_date"
        )
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class ShortRecipeSerializer(serializers.ModelSerializer):
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
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount",)


class RecipesReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта."""
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Favourite.objects.filter(recipe=obj,
                                        user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return ShoppingList.objects.filter(recipe=obj,
                                           user=user).exists()


class RecipesWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    cooking_time = serializers.IntegerField()
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
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                'Нужно выбрать минимум 1 ингредиент!')
        for ingredient in ingredients:
            try:
                int(ingredient.get('amount'))
                if int(ingredient.get('amount')) <= 0:
                    raise ValidationError(
                        'Количество должно быть положительным!')
            except Exception:
                raise ValidationError({'amount': 'Колличество должно'
                                      'быть числом'})
            check_id = ingredient['id']
            check_ingredient = Ingredient.objects.filter(id=check_id)
            if not check_ingredient.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе!')
        return data

    def validate_cooking_time(self, data):
        cooking_time = self.initial_data.get('cooking_time')
        try:
            int(cooking_time)
            if int(cooking_time) < 1:
                raise serializers.ValidationError(
                    'Время готовки не может быть'
                    ' меньше 1!')
            if int(cooking_time) > 720:
                raise serializers.ValidationError(
                    'Время готовки не может быть'
                    ' больше 720!')
        except Exception:
            raise ValidationError({'cooking_time': 'Время'
                                  ' должно быть больше 0'})
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise ValidationError(
                'Рецепт не может быть без тегов'
            )
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f'Тег с id = {tag_id} не существует'
                )
        tags_bd = set(tags)
        if len(tags) != len(tags_bd):
            raise ValidationError('Теги должны быть уникальными')
        return data

    def create_amount_ingredients(self, ingredients):
        amount_ingredients = []
        for ingr in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingr.get('id').id
            )
            ingr, _ = IngredientInRecipe.objects.get_or_create(
                ingredient=ingredient,
                amount=ingredient.get('amount'),
            )
            amount_ingredients.append(ingr)
        return amount_ingredients

    def create(self, validated_data):
        """Метод создания рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        ingredients = self.create_amount_ingredients(ingredients)
        recipe.ingredients.set(ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Метод редактирования рецепта."""
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        ingredients = self.create_amount_ingredients(ingredients)
        instance.ingredients.set(ingredients)
        return super().update(
            instance,
            validated_data
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipesReadSerializer(instance,
                                     context=context).data
