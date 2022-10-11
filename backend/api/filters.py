from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_list = filters.BooleanFilter(
        method="filter_is_in_shopping_list"
    )

    class Meta:
        model = Recipe
        fields = (
            "author",
            "tags",
            "is_favorited",
            "is_in_shopping_list",
        )

    def filter_is_favorited(self, queryset, name, data):
        user = self.request.user
        if data and not user.is_anonymous:
            return queryset.filter(favorite_recipe__user=user)
        return queryset

    def filter_is_in_shopping_list(self, queryset, name, data):
        user = self.request.user
        if data and not user.is_anonymous:
            return queryset.filter(
                shopping_list_recipe__user=user)
        return queryset
