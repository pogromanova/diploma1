from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet

from users.models import User, Subscription
from ..serializers.users import (UserSerializer, SubscriptionSerializer,
                                SubscribeSerializer, AvatarSerializer)
from ..pagination import CustomPagination


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    
    def get_permissions(self):
        # Переопределяем метод получения разрешений
        if self.action == 'retrieve':
            # Для получения профиля пользователя разрешаем всем
            self.permission_classes = [AllowAny]
        elif self.action in ['subscribe', 'subscriptions', 'avatar', 'me']:
            # Для этих действий требуем аутентификацию
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def get_queryset(self):
        return User.objects.all()
    
    def get_instance(self):
        return self.request.user
    
    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(detail=True,
            methods=['post', 'delete'])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            subscription = SubscriptionSerializer(
                author, 
                context={'request': request}
            )
            return Response(subscription.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribers__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            user = request.user
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)