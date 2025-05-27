from django.db.models import Sum
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Recipe, Tag, Ingredient,
                            Favorite, ShoppingCart,
                            RecipeIngredient, ShortLink)
from ..serializers.recipes import (RecipeListSerializer, RecipeCreateSerializer,
                                 IngredientSerializer, TagSerializer,
                                 FavoriteSerializer, ShoppingCartSerializer,
                                 RecipeSerializer)
from ..permissions import IsAuthorOrReadOnly
from ..pagination import CustomPagination
from ..filters import IngredientFilter, RecipeFilter
import logging

logger = logging.getLogger(__name__)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Recipe.objects.all().prefetch_related(
            'tags', 'recipe_ingredients__ingredient'
        ).select_related('author')

    def get_object(self):

        try:
            obj = super().get_object()
            return obj
        except Exception as e:
            logger.error(f"Error in get_object: {e}")
            raise

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in retrieve: {e}")
            raise

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in list: {e}")
            raise

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            data = serializer.data
            
            if 'tags' in data:
                del data['tags']
                
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error in create: {e}")
            raise

    def update(self, request, *args, **kwargs):
        try:
            if request.method == 'PATCH' and 'ingredients' not in request.data:
                return Response(
                    {'errors': 'Поле ingredients является обязательным'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=kwargs.get('partial', False)
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in destroy: {e}")
            raise

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        try:
            recipe = get_object_or_404(Recipe, id=pk)

            if request.method == 'POST':
                serializer = FavoriteSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                recipe_serializer = RecipeSerializer(
                    recipe, context={'request': request}
                )
                return Response(recipe_serializer.data, 
                            status=status.HTTP_201_CREATED)

            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                logger.error(f"Recipe {pk} not in favorites for user {user.id}")
                return Response(
                    {'errors': 'Рецепт не в избранном!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in favorite action: {e}")
            raise

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        try:
            recipe = get_object_or_404(Recipe, id=pk)

            if request.method == 'POST':
                serializer = ShoppingCartSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                recipe_serializer = RecipeSerializer(
                    recipe, context={'request': request}
                )
                return Response(recipe_serializer.data, 
                            status=status.HTTP_201_CREATED)

            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart_item.exists():
                logger.error(f"Recipe {pk} not in shopping cart for user {user.id}")
                return Response(
                    {'errors': 'Рецепт не в списке покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in shopping_cart action: {e}")
            raise

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        try:
            if not ShoppingCart.objects.filter(user=user).exists():
                logger.error(f"Shopping cart is empty for user {user.id}")
                return Response(
                    {'errors': 'Список покупок пуст!'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ingredients = RecipeIngredient.objects.filter(
                recipe__in_shopping_cart__user=user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(amount=Sum('amount'))

            shopping_list = 'Список покупок:\n\n'
            for item in ingredients:
                shopping_list += (
                    f"{item['ingredient__name']} "
                    f"({item['ingredient__measurement_unit']}) — "
                    f"{item['amount']}\n"
                )

            response = HttpResponse(shopping_list, content_type='text/plain')
            response['Content-Disposition'] = (
                'attachment; filename="shopping_cart.txt"'
            )
            return response
        except Exception as e:
            logger.error(f"Error in download_shopping_cart action: {e}")
            raise
    @action(detail=True,
        methods=['get'],
        url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        
        short_link = ShortLink.objects.filter(recipe=recipe).first()
        
        if not short_link:
            while True:
                short_id = ShortLink.generate_short_id(recipe.id)
                if not ShortLink.objects.filter(short_id=short_id).exists():
                    break
            
            short_link = ShortLink.objects.create(
                recipe=recipe,
                short_id=short_id
            )
        
        domain = request.build_absolute_uri('/').rstrip('/')
        full_short_link = f"{domain}/s/{short_link.short_id}"
        
        return Response({"short-link": full_short_link})

def redirect_short_link(request, short_id):

    short_link = get_object_or_404(ShortLink, short_id=short_id)
    return redirect(f'/recipes/{short_link.recipe.id}/')  

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
            total_count = Recipe.objects.count()
            logger.info(f"Total recipes in database: {total_count}")
            
            queryset = self.filter_queryset(self.get_queryset())
            filtered_count = queryset.count()
            logger.info(f"Filtered recipes count: {filtered_count}")

            if request.query_params:
                logger.info(f"Active filters: {request.query_params}")
                
            page = self.paginate_queryset(queryset)
            if page is not None:
                logger.info(f"Page size: {len(page)}")
                serializer = self.get_serializer(page, many=True)
                logger.info(f"Serialized data count: {len(serializer.data)}")
                if serializer.data:
                    logger.info(f"First item preview: {serializer.data[0]}")
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"Serialized data count (no pagination): {len(serializer.data)}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in list: {e}", exc_info=True)
            raise
    
    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in IngredientViewSet retrieve: {e}")
            raise


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in TagViewSet list: {e}")
            raise
    
    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in TagViewSet retrieve: {e}")
            raise