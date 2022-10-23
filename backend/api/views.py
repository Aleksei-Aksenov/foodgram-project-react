from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated)
from rest_framework.response import Response

from recipes.models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingList, Tag)
from users.models import Follow, User
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (CustomUserSerializer, FollowSerializer,
                          IngredientSerializer, RecipesReadSerializer,
                          RecipesWriteSerializer, FavoriteSerializer,
                          TagSerializer)


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингридиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Метод для просмотра подписок на авторов."""
        user = self.request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Метод для подписки/отписки от автора."""
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if request.user.id == author.id:
                raise ValidationError(
                    "Вы не можете подписаться сами на себя!"
                )
            else:
                serializer = FollowSerializer(
                    Follow.objects.create(user=request.user, author=author),
                    context={"request": request},
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        elif request.method == "DELETE":
            if Follow.objects.filter(
                user=request.user, author=author
            ).exists():
                Follow.objects.filter(
                    user=request.user, author=author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"errors": "Автор отсутсвует в списке подписок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецепта."""
    queryset = Recipe.objects.all().order_by("-id")
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter
    serializer_class = RecipesReadSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    def add_recipe(self, model, user, pk):
        """Метод для добавления"""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = FavoriteSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, user, pk):
        """Метод для удаления"""
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален'
        }, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="favorite",
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        """Метод для добавления/удаления из избранного."""
        if request.method == "POST":
            return self.add_recipe(Favourite, request.user, pk)
        else:
            return self.delete_recipe(Favourite, request.user, pk)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        """Метод для добавления/удаления из списка покупок."""
        if request.method == "POST":
            return self.add_recipe(ShoppingList, request.user, pk)
        else:
            return self.delete_recipe(ShoppingList, request.user, pk)

    @action(
        detail=False,
        methods=["GET"],
        url_path="download_shopping_cart",
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания рецепта."""
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_list_recipe__user=request.user).values(
            "ingredient__name",
            "ingredient__measurement_unit").annotate(total=Sum("amount"))

        shopping_cart = '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["total"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        filename = "shopping_cart.txt"
        response = HttpResponse(shopping_cart, content_type="text/plain")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
