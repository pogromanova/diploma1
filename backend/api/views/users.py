from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from ..serializers.users import (UserSerializer, SubscriptionSerializer,
                              SubscribeSerializer, AvatarSerializer, 
                              User, Subscription)
from ..pagination import CustomPagination
import logging

logger = logging.getLogger(__name__)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    
    def get_instance(self):
        return self.request.user
    
    def get_queryset(self):
        user_objects = User.objects.all()
        return user_objects
    
    def get_permissions(self):
        permission_classes = []
        current_action = self.action
        
        if current_action == 'retrieve':
            permission_classes = [AllowAny]
        elif current_action in ['subscribe', 'subscriptions', 'avatar', 'me']:
            permission_classes = [IsAuthenticated]
            
        self.permission_classes = permission_classes
        return super().get_permissions()
    
    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        result = self.retrieve(request, *args, **kwargs)
        return result
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        try:
            target_author = self.get_object()
            current_user = request.user
            
            if request.method == 'POST':
                self_subscribe = current_user == target_author
                if self_subscribe:
                    error_msg = {'errors': 'Нельзя подписаться на самого себя'}
                    return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
                
                already_subscribed = current_user.subscriptions.filter(
                    author=target_author
                ).exists()
                if already_subscribed:
                    error_msg = {'errors': 'Вы уже подписаны на этого пользователя'}
                    return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
                
                Subscription.objects.create(user=current_user, author=target_author)
                subscription_data = SubscriptionSerializer(
                    target_author, context={'request': request}
                )
                return Response(subscription_data.data, status=status.HTTP_201_CREATED)
            
            subscription_obj = current_user.subscriptions.filter(author=target_author)
            if subscription_obj.count() == 0:
                error_msg = {'errors': 'Вы не подписаны на этого пользователя'}
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
            
            subscription_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            logger.error(f"Error in subscribe action: {exc}")
            raise
    
    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        try:
            current_user = request.user
            user_subscriptions = User.objects.filter(
                subscribers__user=current_user
            ).prefetch_related('subscribers')
            
            paginated_subscriptions = self.paginate_queryset(user_subscriptions)
            if paginated_subscriptions is not None:
                subscription_data = SubscriptionSerializer(
                    paginated_subscriptions, many=True, 
                    context={'request': request}
                )
                return self.get_paginated_response(subscription_data.data)
            
            subscription_data = SubscriptionSerializer(
                user_subscriptions, many=True, 
                context={'request': request}
            )
            return Response(subscription_data.data)
        except Exception as exc:
            logger.error(f"Error in subscriptions action: {exc}")
            raise
            
    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            avatar_serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
                context={'request': request}
            )
            avatar_serializer.is_valid(raise_exception=True)
            avatar_serializer.save()
            return Response(avatar_serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            current_user = request.user
            has_avatar = bool(current_user.avatar)
            
            if has_avatar:
                current_user.avatar.delete()
                current_user.avatar = None
                current_user.save()
                
            return Response(status=status.HTTP_204_NO_CONTENT)