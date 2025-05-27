from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipes.models import Recipe
from users.models import Subscription
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
import base64
import uuid
from django.core.files.base import ContentFile

User = get_user_model()


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
    
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
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
        request = self.context.get('request')
        if instance.avatar and hasattr(instance.avatar, 'url'):
            return {
                'avatar': request.build_absolute_uri(instance.avatar.url)
            }
        return {'avatar': None}
        
    def validate_avatar(self, value):
        """
        Проверяем, что value - это строка base64 с префиксом данных.
        """
        if not value or not isinstance(value, str):
            raise serializers.ValidationError('Некорректный формат данных')
            
        if 'data:' not in value or ';base64,' not in value:
            raise serializers.ValidationError('Строка не соответствует формату data:mime;base64,')
            
        return value
        
    def update(self, instance, validated_data):
        avatar_data = validated_data.get('avatar')
        
        # Разбиваем строку на формат и данные
        format, imgstr = avatar_data.split(';base64,')
        # Получаем расширение файла из формата
        ext = format.split('/')[-1]
        
        # Создаем уникальное имя файла
        file_name = f"{uuid.uuid4()}.{ext}"
        
        # Декодируем base64 и сохраняем в файл
        data = ContentFile(base64.b64decode(imgstr), name=file_name)
        
        # Если у пользователя уже есть аватар - удаляем его
        if instance.avatar:
            instance.avatar.delete()
            
        # Сохраняем новый аватар
        instance.avatar = data
        instance.save()
        
        return instance