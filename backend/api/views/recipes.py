from django.db.models import Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Recipe, Ingredient, Tag, 
                          Favorite, ShoppingCart,
                          RecipeIngredient, ShortLink)
from ..serializers.recipes import (RecipeListSerializer, RecipeCreateSerializer,
                                TagSerializer, IngredientSerializer,
                                FavoriteSerializer, ShoppingCartSerializer,
                                RecipeSerializer)
from ..pagination import CustomPagination
from ..permissions import IsAuthorOrReadOnly
from ..filters import RecipeFilter, IngredientFilter
import logging

logger = logging.getLogger(__name__)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if SAFE_METHODS.__contains__(self.request.method):
            return RecipeListSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        query = Recipe.objects.all().prefetch_related(
            'tags', 'recipe_ingredients__ingredient'
        ).select_related('author')
        return query

    def get_object(self):
        try:
            return super().get_object()
        except Exception as exc:
            logger.error(f"Error in get_object: {exc}")
            raise

    def retrieve(self, request, *args, **kwargs):
        try:
            result = super().retrieve(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in retrieve: {exc}")
            raise

    def list(self, request, *args, **kwargs):
        try:
            result = super().list(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in list: {exc}")
            raise

    def create(self, request, *args, **kwargs):
        try:
            data_serializer = self.get_serializer(data=request.data)
            data_serializer.is_valid(raise_exception=True)
            self.perform_create(data_serializer)
            headers = self.get_success_headers(data_serializer.data)
            result_data = data_serializer.data
            
            if result_data.get('tags'):
                result_data.pop('tags')
                
            return Response(result_data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as exc:
            logger.error(f"Error in create: {exc}")
            raise

    def update(self, request, *args, **kwargs):
        try:
            is_patch = request.method == 'PATCH'
            has_ingredients = 'ingredients' in request.data
            
            if is_patch and not has_ingredients:
                error_msg = {'errors': 'Поле ingredients является обязательным'}
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
                
            obj = self.get_object()
            partial = kwargs.get('partial', False)
            data_serializer = self.get_serializer(obj, data=request.data, partial=partial)
            data_serializer.is_valid(raise_exception=True)
            self.perform_update(data_serializer)
            return Response(data_serializer.data)
        except Exception as exc:
            logger.error(f"Error in update: {exc}")
            raise

    def destroy(self, request, *args, **kwargs):
        try:
            result = super().destroy(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in destroy: {exc}")
            raise

    @action(detail=True, methods=['post', 'delete'], 
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        current_user = request.user
        try:
            current_recipe = get_object_or_404(Recipe, id=pk)

            if request.method == 'POST':
                data = {'user': current_user.id, 'recipe': current_recipe.id}
                favorite_serializer = FavoriteSerializer(
                    data=data, context={'request': request}
                )
                favorite_serializer.is_valid(raise_exception=True)
                favorite_serializer.save()
                
                recipe_data = RecipeSerializer(
                    current_recipe, context={'request': request}
                )
                return Response(recipe_data.data, status=status.HTTP_201_CREATED)

            favorite_item = Favorite.objects.filter(
                user=current_user, recipe=current_recipe
            )
            if favorite_item.count() == 0:
                logger.error(f"Recipe {pk} not in favorites for user {current_user.id}")
                error_msg = {'errors': 'Рецепт не в избранном!'}
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
                
            favorite_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            logger.error(f"Error in favorite action: {exc}")
            raise

    @action(detail=True, methods=['post', 'delete'], 
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        current_user = request.user
        try:
            current_recipe = get_object_or_404(Recipe, id=pk)

            if request.method == 'POST':
                cart_data = {'user': current_user.id, 'recipe': current_recipe.id}
                cart_serializer = ShoppingCartSerializer(
                    data=cart_data, context={'request': request}
                )
                cart_serializer.is_valid(raise_exception=True)
                cart_serializer.save()
                
                recipe_data = RecipeSerializer(
                    current_recipe, context={'request': request}
                )
                return Response(recipe_data.data, status=status.HTTP_201_CREATED)

            cart_items = ShoppingCart.objects.filter(
                user=current_user, recipe=current_recipe
            )
            if not cart_items.exists():
                logger.error(f"Recipe {pk} not in shopping cart for user {current_user.id}")
                error_msg = {'errors': 'Рецепт не в списке покупок!'}
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
                
            cart_items.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            logger.error(f"Error in shopping_cart action: {exc}")
            raise

    @action(detail=False, permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        current_user = request.user
        try:
            cart_exists = ShoppingCart.objects.filter(user=current_user).exists()
            if not cart_exists:
                logger.error(f"Shopping cart is empty for user {current_user.id}")
                error_msg = {'errors': 'Список покупок пуст!'}
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

            ingredients_list = RecipeIngredient.objects.filter(
                recipe__in_shopping_cart__user=current_user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(total_amount=Sum('amount'))

            content = 'Список покупок:\n\n'
            for ingredient in ingredients_list:
                content += (
                    f"{ingredient['ingredient__name']} "
                    f"({ingredient['ingredient__measurement_unit']}) — "
                    f"{ingredient['total_amount']}\n"
                )

            file_response = HttpResponse(content, content_type='text/plain')
            file_response['Content-Disposition'] = (
                'attachment; filename="shopping_cart.txt"'
            )
            return file_response
        except Exception as exc:
            logger.error(f"Error in download_shopping_cart action: {exc}")
            raise
            
    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        current_recipe = self.get_object()
        
        link_object = ShortLink.objects.filter(recipe=current_recipe).first()
        
        if link_object is None:
            while True:
                new_short_id = ShortLink.generate_short_id(current_recipe.id)
                exists = ShortLink.objects.filter(short_id=new_short_id).exists()
                if not exists:
                    break
            
            link_object = ShortLink.objects.create(
                recipe=current_recipe,
                short_id=new_short_id
            )
        
        base_url = request.build_absolute_uri('/').rstrip('/')
        full_url = f"{base_url}/s/{link_object.short_id}"
        
        return Response({"short-link": full_url})

def redirect_short_link(request, short_id):
    link_object = get_object_or_404(ShortLink, short_id=short_id)
    target_url = f'/recipes/{link_object.recipe.id}/'
    return redirect(target_url)  

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None
    
    def list(self, request, *args, **kwargs):
        logger.info(f"list called with params: {request.query_params}")
        try:
            recipe_count = Recipe.objects.count()
            logger.info(f"Total recipes in database: {recipe_count}")
            
            filtered_queryset = self.filter_queryset(self.get_queryset())
            result_count = filtered_queryset.count()
            logger.info(f"Filtered recipes count: {result_count}")

            if len(request.query_params) > 0:
                logger.info(f"Active filters: {request.query_params}")
                
            paginated_data = self.paginate_queryset(filtered_queryset)
            if paginated_data:
                logger.info(f"Page size: {len(paginated_data)}")
                result_serializer = self.get_serializer(paginated_data, many=True)
                logger.info(f"Serialized data count: {len(result_serializer.data)}")
                if len(result_serializer.data) > 0:
                    logger.info(f"First item preview: {result_serializer.data[0]}")
                return self.get_paginated_response(result_serializer.data)

            result_serializer = self.get_serializer(filtered_queryset, many=True)
            logger.info(f"Serialized data count (no pagination): {len(result_serializer.data)}")
            return Response(result_serializer.data)
        except Exception as exc:
            logger.error(f"Error in list: {exc}", exc_info=True)
            raise
    
    def retrieve(self, request, *args, **kwargs):
        try:
            result = super().retrieve(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in IngredientViewSet retrieve: {exc}")
            raise


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    
    def list(self, request, *args, **kwargs):
        try:
            result = super().list(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in TagViewSet list: {exc}")
            raise
    
    def retrieve(self, request, *args, **kwargs):
        try:
            result = super().retrieve(request, *args, **kwargs)
            return result
        except Exception as exc:
            logger.error(f"Error in TagViewSet retrieve: {exc}")
            raise