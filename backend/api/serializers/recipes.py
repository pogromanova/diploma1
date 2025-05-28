from rest_framework import serializers
from django.db import transaction
import base64
from django.core.files.base import ContentFile
import logging

from recipes.models import (Recipe, Tag, Ingredient, 
                          RecipeIngredient, Favorite,
                          ShoppingCart, User)
from api.serializers.users import UserSerializer

logger = logging.getLogger(__name__)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                img_parts = data.split(';base64,')
                img_format = img_parts[0]
                img_str = img_parts[1]
                ext = img_format.split('/')[-1]
                decoded = ContentFile(base64.b64decode(img_str), name=f'temp.{ext}')
                return super().to_internal_value(decoded)
            except Exception:
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
            image_url = obj.image.url
            if request:
                image_url = request.build_absolute_uri(image_url)
            return image_url
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
        representation = super().to_representation(instance)
        
        if 'tags' in representation:
            del representation['tags']
            
        return representation

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            img_url = obj.image.url
            if request:
                img_url = request.build_absolute_uri(img_url)
            logger.debug(f"Recipe {obj.id}: image URL = {img_url}")
            return img_url
        logger.warning(f"Recipe {obj.id}: no image available")
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            is_fav = False
        else:
            is_fav = Favorite.objects.filter(
                user=request.user, 
                recipe=obj
            ).exists()
        logger.debug(f"Recipe {obj.id}: is_favorited = {is_fav}")
        return is_fav

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            in_cart = False
        else:
            in_cart = ShoppingCart.objects.filter(
                user=request.user, 
                recipe=obj
            ).exists()
        logger.debug(f"Recipe {obj.id}: is_in_shopping_cart = {in_cart}")
        return in_cart


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
        if len(value) == 0:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        
        seen_ids = set()
        for ingredient_item in value:
            ingredient_id = ingredient_item['id'].id
            if ingredient_id in seen_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!'
                )
            seen_ids.add(ingredient_id)
                
        return value

    def create_ingredients(self, recipe, ingredients):
        ingredients_list = []
        for ing_data in ingredients:
            ingredients_list.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ing_data['id'],
                    amount=ing_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        
        new_recipe = Recipe.objects.create(**validated_data)
        
        if len(tags_data) > 0:
            new_recipe.tags.set(tags_data)
            
        self.create_ingredients(new_recipe, ingredients_data)
        return new_recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            new_ingredients = validated_data.pop('ingredients')
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, new_ingredients)
            
        if 'tags' in validated_data:
            new_tags = validated_data.pop('tags')
            instance.tags.set(new_tags)
            
        for field_name, field_value in validated_data.items():
            setattr(instance, field_name, field_value)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        context_data = {'request': self.context.get('request')}
        return RecipeListSerializer(
            instance,
            context=context_data
        ).data
    

class ShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField(source='short-link')

    class Meta:
        fields = ('short-link',)