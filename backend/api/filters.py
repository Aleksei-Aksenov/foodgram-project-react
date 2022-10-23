from django.db.models import IntegerField, Value
from django_filters.rest_framework import (AllValuesMultipleFilter,
                                           BooleanFilter, CharFilter,
                                           FilterSet)

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = [
            'author',
        ]

    def get_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(
                favorite_recipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(
                shopping_list_recipe__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(method='search_by_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def search_by_name(self, queryset, name, value):
        if not value:
            return queryset
        start_with_queryset = (
            queryset.filter(name__istartswith=value).annotate(
                order=Value(0, IntegerField())
            )
        )
        contain_queryset = (
            queryset.filter(name__icontains=value).exclude(
                pk__in=(start_with_queryset.values_list('id', flat=True))
            ).annotate(order=Value(1, IntegerField()))
        )
        return start_with_queryset.union(contain_queryset).order_by('order')
