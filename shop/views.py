from django.db.models import Q, Prefetch
from django.db.models.functions import Lower
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True).select_related('parent')
    serializer_class = CategorySerializer

    def get_queryset(self):
        return self.queryset.order_by('tree_id', 'lft')


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category')

        search_query = self.request.query_params.get('search')  # Новый параметр поиска
        sort = self.request.query_params.get('ordering', 'default')

        has_filters = (
                category_slug is not None or
                search_query is not None or
                bool(self.request.query_params.getlist('brand')) or
                bool(self.request.query_params.getlist('size')) or
                'in_stock' in self.request.query_params
        )

        # Фильтрация по поисковому запросу
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                descendants = category.get_descendants(include_self=True)
                queryset = queryset.filter(
                    productcategory__category__in=descendants
                ).distinct()
            except Category.DoesNotExist:
                return queryset.none()

        brands = self.request.query_params.getlist('brand')
        if brands:
            queryset = queryset.filter(brand__slug__in=brands)

        # Фильтрация по размерам
        sizes = self.request.query_params.getlist('size')
        # Фильтрация по наличию
        in_stock = self.request.query_params.get('in_stock') == 'true'

        # Если выбраны размеры И фильтр "В наличии"
        if sizes and in_stock:
            try:
                sizes_float = [float(size) for size in sizes]
                # Фильтруем по выбранным размерам и наличию именно этих размеров
                queryset = queryset.filter(
                    models__sizes__size__in=sizes_float,
                    models__sizes__stock__gt=0
                ).distinct()
            except ValueError:
                pass
        # Если выбраны только размеры (без фильтра наличия)
        elif sizes:
            try:
                sizes_float = [float(size) for size in sizes]
                queryset = queryset.filter(
                    models__sizes__size__in=sizes_float
                ).distinct()
            except ValueError:
                pass
        # Если выбран только фильтр "В наличии" (без конкретных размеров)
        elif in_stock:
            # Фильтруем товары с любым размером в наличии
            queryset = queryset.filter(
                models__sizes__stock__gt=0
            ).distinct()

        if not has_filters and sort == 'default':
            queryset = queryset.order_by('?')
        else:
            if sort == 'base_price':
                queryset = queryset.order_by('base_price')
            elif sort == '-base_price':
                queryset = queryset.order_by('-base_price')
            elif sort == 'title':
                queryset = queryset.annotate(lower_title=Lower('title')).order_by('lower_title')
            elif sort == 'default':
                queryset = queryset.order_by('id')

        return queryset.prefetch_related(
            Prefetch('models', queryset=ProductModel.objects.filter(is_active=True).prefetch_related(
                'sizes',
                'images'
            )),
            'brand'
        )

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        product = self.get_object()
        models = product.models.filter(is_active=True)
        serializer = ProductModelSerializer(models, many=True)
        return Response(serializer.data)

class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    pagination_class = None  # Отключаем пагинацию для брендов