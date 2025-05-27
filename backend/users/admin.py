from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .models import Subscription

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 
        'username', 
        'email', 
        'first_name',
        'last_name', 
        'is_staff',
        'display_avatar'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'username', 
                'first_name', 
                'last_name', 
                'password1', 
                'password2'
            )
        }),
    )
    
    def display_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="30" height="30" />', obj.avatar.url)
        return "-"
    display_avatar.short_description = 'Аватар'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')