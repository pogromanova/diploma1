import django_filters as filters
from django.db.models import Q
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag, Ingredient


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')
    
    def filter_name(self, queryset, name, value):
        filtered_qs = queryset.filter(name__istartswith=value)
        return filtered_qs

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        current_user = self.request.user
        if not current_user.is_authenticated:
            return queryset
        if value == 1:
            return queryset.filter(in_favorites__user=current_user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        current_user = self.request.user
        user_authenticated = current_user.is_authenticated
        if value == 1 and user_authenticated:
            filtered = queryset.filter(in_shopping_cart__user=current_user)
            return filtered
        return queryset