from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Recipe
from rest_framework import serializers

from .models import Follow

User = get_user_model()


class UserRegistrationSerializer(UserCreateSerializer):
    """Cериализатор регистрации"""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели пользователя"""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """ Метод обработки параметра is_subscribed"""
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class SubscribeUserSerializer(serializers.ModelSerializer):
    """Сериализатор вывода авторов на которых подписан текущий пользователь.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        """Валидатор подписки на пользователя"""
        user = self.context.get('request').user
        following_id = self.data.get['author'].id
        if Follow.objects.filter(user=user,
                                 following__id=following_id).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя')
        if user.id == following_id:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        if user.id is None:
            raise serializers.ValidationError(
                'Пользователь не существует')
        return data


class FollowingRecipesSerializers(serializers.ModelSerializer):
    """Сериализатор списка рецептов подписанных авторов"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowViewSerializer(serializers.ModelSerializer):
    """Сериализатор подписок"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """ Метод обработки параметра is_subscribed"""
        if not self.context.get('request').user.is_authenticated:
            return False
        return Follow.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    def get_recipes(self, obj):
        """Метод получения данных рецептов автора"""
        recipes_limit = int(self.context['request'].GET.get(
            'recipes_limit', 10))
        user = get_object_or_404(User, pk=obj.pk)
        recipes = Recipe.objects.filter(author=user)[:recipes_limit]

        return FollowingRecipesSerializers(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Метод подсчета количества рецептов автора."""
        user = get_object_or_404(User, pk=obj.pk)
        return Recipe.objects.filter(author=user).count()
