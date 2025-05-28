from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
import uuid
import logging
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Subscription

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_avatar(self, obj):
        has_avatar = obj.avatar and hasattr(obj.avatar, 'url')
        if has_avatar:
            current_request = self.context.get('request')
            if current_request:
                return current_request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        current_request = self.context.get('request')
        if not current_request or not current_request.user.is_authenticated:
            return False
        return current_request.user.subscriptions.filter(author=obj).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
    
    def get_image(self, obj):
        current_request = self.context.get('request')
        has_image = obj.image and hasattr(obj.image, 'url')
        if has_image and current_request:
            return current_request.build_absolute_uri(obj.image.url)
        return None


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        current_request = self.context.get('request')
        limit_param = current_request.query_params.get('recipes_limit')
        
        recipes_queryset = obj.recipes.all()
        if limit_param and limit_param.isdigit():
            recipes_queryset = recipes_queryset[:int(limit_param)]
            
        serializer_context = {'request': current_request}
        return RecipeShortSerializer(
            recipes_queryset, 
            many=True, 
            context=serializer_context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        current_user = data['user']
        author_obj = data['author']
        
        if current_user.id == author_obj.id:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
            
        if Subscription.objects.filter(user=current_user, author=author_obj).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
            
        return data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        current_request = self.context.get('request')
        has_avatar = instance.avatar and hasattr(instance.avatar, 'url')
        
        if has_avatar:
            avatar_url = instance.avatar.url
            if current_request:
                avatar_url = current_request.build_absolute_uri(avatar_url)
            return {'avatar': avatar_url}
            
        return {'avatar': None}
        
    def validate_avatar(self, value):
        is_valid_type = value and isinstance(value, str)
        if not is_valid_type:
            raise serializers.ValidationError('Некорректный формат данных')
        
        has_valid_format = 'data:' in value and ';base64,' in value
        if not has_valid_format:
            raise serializers.ValidationError('Строка не соответствует формату data:mime;base64,')
            
        return value

    def update(self, instance, validated_data):
        avatar_string = validated_data.get('avatar')
        
        format_part, data_part = avatar_string.split(';base64,')
        extension = format_part.split('/')[-1]
        
        unique_filename = f"{uuid.uuid4()}.{extension}"
        
        avatar_content = ContentFile(
            base64.b64decode(data_part), 
            name=unique_filename
        )
        
        if instance.avatar:
            instance.avatar.delete()
            
        instance.avatar = avatar_content
        instance.save()
        
        return instance