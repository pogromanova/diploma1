from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin

from .models import (
    User, Tag, Ingredient, Recipe,
    RecipeIngredient, Favorite, ShoppingCart,
    ShortLink, Subscription
)


class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name', 
        'is_staff', 'show_avatar'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Аватар пользователя', {'fields': ('avatar',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 
                'first_name', 'last_name', 
                'password1', 'password2'
            )
        }),
    )
    
    def show_avatar(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />', 
                obj.avatar.url
            )
        return "—"
    show_avatar.short_description = 'Аватар'


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'show_color', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    
    def show_color(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; '
            'display: inline-block; border: 1px solid #ccc; margin-right: 5px;"></div> {}',
            obj.color, obj.color
        )
    show_color.short_description = 'Цвет'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_using')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(recipes_using_count=Count('recipes'))
    
    def recipes_using(self, obj):
        return obj.recipes_using_count
    recipes_using.short_description = 'Используется в рецептах'
    recipes_using.admin_order_field = 'recipes_using_count'


class IngredientInlineAdmin(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1
    autocomplete_fields = ['ingredient']


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 
        'favorites_count', 'ingredient_count', 'show_image'
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'tags', 'pub_date')
    readonly_fields = ('pub_date', 'show_image')
    filter_horizontal = ('tags',)
    inlines = (IngredientInlineAdmin,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(fav_count=Count('in_favorites'))
    
    def favorites_count(self, obj):
        return obj.fav_count
    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = 'fav_count'
    
    def ingredient_count(self, obj):
        return obj.recipe_ingredients.count()
    ingredient_count.short_description = 'Количество ингредиентов'
    
    def show_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />', 
                obj.image.url
            )
        return "Нет изображения"
    show_image.short_description = 'Изображение'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_id', 'recipe', 'created_at')
    search_fields = ('short_id', 'recipe__name')
    list_filter = ('created_at',)
    readonly_fields = ('short_id', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')


admin.site.register(User, CustomUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(ShortLink, ShortLinkAdmin)
admin.site.register(Subscription, SubscriptionAdmin)