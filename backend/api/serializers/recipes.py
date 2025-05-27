from rest_framework import serializers
from django.db import transaction
from django.core.files.base import ContentFile
import base64

from recipes.models import (Recipe, Tag, Ingredient,
                           RecipeIngredient, Favorite,
                           ShoppingCart)

from users.models import User
from api.serializers.users import UserSerializer

import logging
logger = logging.getLogger(__name__)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
            except Exception as e:
                raise serializers.ValidationError("Invalid image data")

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное!'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок!'
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
    
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

class RecipeListSerializer(serializers.ModelSerializer):

    
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def to_representation(self, instance):

        logger.info(f"Serializing recipe {instance.id}: {instance.name}")
        data = super().to_representation(instance)
        
        if 'tags' in data:
            del data['tags']
            
        return data

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = request.build_absolute_uri(obj.image.url) if request else obj.image.url
            logger.debug(f"Recipe {obj.id}: image URL = {url}")
            return url
        logger.warning(f"Recipe {obj.id}: no image available")
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        result = Favorite.objects.filter(user=request.user, recipe=obj).exists()
        logger.debug(f"Recipe {obj.id}: is_favorited = {result}")
        return result

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        result = ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        logger.debug(f"Recipe {obj.id}: is_in_shopping_cart = {result}")
        return result

class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!'
            )
                
        return value

    def create_ingredients(self, recipe, ingredients):
        recipe_ingredients = []
        for item in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item['id'],
                    amount=item['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])
        
        recipe = Recipe.objects.create(**validated_data)
        
        if tags:
            recipe.tags.set(tags)
            
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients)
            
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data
    
class ShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField(source='short-link')

    class Meta:
        fields = ('short-link',)