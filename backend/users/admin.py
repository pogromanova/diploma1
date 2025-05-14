# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from .models import Subscription

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Настройка админ-панели для пользователей."""
    list_display = (
        'id', 
        'username', 
        'email', 
        'first_name',
        'last_name', 
        'is_staff'
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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка админ-панели для подписок."""
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related('user', 'author')