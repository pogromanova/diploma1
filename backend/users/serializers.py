from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField

from .models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        
    def validate_username(self, value):
        import re
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Username contains invalid characters'
            )
        return value


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.is_anonymous:
                return False
            return Subscription.objects.filter(
                user=user,
                author=obj
            ).exists()
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if instance.avatar:
            if request:
                data['avatar'] = request.build_absolute_uri(instance.avatar.url)
            else:
                data['avatar'] = instance.avatar.url
        else:
            data['avatar'] = None
            
        return data


class RecipeShortSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(read_only=True)
    
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )
        read_only_fields = tuple(fields)  

    def get_recipes_count(self, obj):
        return obj.recipes.count()
    
    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    limit = int(recipes_limit)
                except (ValueError, TypeError):
                    pass
        
        recipes = obj.recipes.all()
        if limit is not None and limit > 0:
            recipes = recipes[:limit]
            
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data