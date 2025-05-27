from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..serializers.users import (UserSerializer, SubscriptionSerializer,
                                SubscribeSerializer, AvatarSerializer)
from users.models import User, Subscription
from ..pagination import CustomPagination
import logging

logger = logging.getLogger(__name__)


class UserViewSet(DjoserUserViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    
    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [AllowAny]
        elif self.action in ['subscribe', 'subscriptions', 'avatar', 'me']:
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
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):

        try:
            author = self.get_object()
            user = request.user
            
            if request.method == 'POST':
                if user == author:
                    return Response(
                        {'errors': 'Нельзя подписаться на самого себя'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if user.subscriptions.filter(author=author).exists():
                    return Response(
                        {'errors': 'Вы уже подписаны на этого пользователя'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                Subscription.objects.create(user=user, author=author)
                serializer = SubscriptionSerializer(
                    author, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            # Обработка метода DELETE
            subscription = user.subscriptions.filter(author=author)
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in subscribe action: {e}")
            raise
    
    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):

        try:
            user = request.user
            subscriptions = User.objects.filter(
                subscribers__user=user
            ).prefetch_related('subscribers')
            
            page = self.paginate_queryset(subscriptions)
            if page is not None:
                serializer = SubscriptionSerializer(
                    page, many=True, context={'request': request}
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = SubscriptionSerializer(
                subscriptions, many=True, context={'request': request}
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in subscriptions action: {e}")
            raise
            
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