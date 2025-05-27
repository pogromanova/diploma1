import django_filters as filters
from django.db.models import Q
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag, Ingredient


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)
    
    def filter_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author__id')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(in_favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')