# backend/users/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model

from .models import Subscription
from .serializers import (
    SubscriptionSerializer, 
    CustomUserSerializer
)
from recipes.pagination import CustomPagination

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    
    def get_permissions(self):
        """Установка прав доступа для различных действий."""
        if self.action == 'me':
            return [IsAuthenticated()]
        elif self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()
    
    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user
        
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Обязательное поле.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Возвращаем только поле avatar
            return Response({'avatar': serializer.data.get('avatar')})
        
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Управление подписками на авторов."""
        user = request.user
        author = get_object_or_404(User, id=id)
        
        if request.method == 'POST':
            # Проверка на подписку на себя
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверка существующей подписки
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Создание подписки
            Subscription.objects.create(user=user, author=author)
            
            # Сериализация и возврат данных автора
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            # Удаление подписки
            subscription = Subscription.objects.filter(
                user=user,
                author=author
            )
            
            if not subscription.exists():
                return Response(
                    {'detail': 'Вы не подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        
        # Получаем авторов, на которых подписан пользователь
        subscriptions = User.objects.filter(
            subscribers__user=user
        )
        
        # Применяем пагинацию
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        # Если пагинация не применяется
        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)