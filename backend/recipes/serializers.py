import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)
from users.serializers import CustomUserSerializer

User = get_user_model()


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


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False 
    )
    image = Base64ImageField(required=True)  
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        if 'image' not in data or not data['image']:
            raise serializers.ValidationError({
                'image': ['Это поле обязательно.']
            })
        if not data.get('ingredients'):
            raise serializers.ValidationError({
                'ingredients': ['Обязательное поле.']
            })
        
        if 'tags' in data and not data['tags']:
            raise serializers.ValidationError({
                'tags': ['Обязательное поле.']
            })
            
        ingredient_ids = []
        for item in data['ingredients']:
            ingredient_id = item['id'].id if hasattr(item['id'], 'id') else item['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError({
                    'ingredients': ['Ингредиенты должны быть уникальными!']
                })
            ingredient_ids.append(ingredient_id)
        
        if 'tags' in data and data['tags']:
            tag_ids = [tag.id if hasattr(tag, 'id') else tag for tag in data['tags']]
            if len(tag_ids) != len(set(tag_ids)):
                raise serializers.ValidationError({
                    'tags': ['Теги должны быть уникальными!']
                })
        
        return data

    def create_ingredients(self, recipe, ingredients):
        recipe_ingredients = []
        for ingredient_data in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])
        
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        
        return recipe

    def update(self, instance, validated_data):
        if 'image' in validated_data and not validated_data['image']:
            raise serializers.ValidationError({
                'image': ['Это поле не может быть пустым.']
            })
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients)
            
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
            
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if instance.image and request:
            data['image'] = request.build_absolute_uri(instance.image.url)
        
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if instance.image:
            data['image'] = request.build_absolute_uri(instance.image.url)
        
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if Favorite.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном!'
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if ShoppingCart.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже в списке покупок!'
            )
        return data