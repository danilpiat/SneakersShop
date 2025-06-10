from django.db.models import Q, Prefetch
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
        if sizes:
            # Преобразуем размеры в числа с плавающей точкой
            try:
                sizes_float = [float(size) for size in sizes]
                queryset = queryset.filter(
                    models__sizes__size__in=sizes_float
                ).distinct()
            except ValueError:
                pass

        # Фильтрация по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price and max_price:
            try:
                min_price_float = float(min_price)
                max_price_float = float(max_price)
                queryset = queryset.filter(
                    base_price__gte=min_price_float,
                    base_price__lte=max_price_float
                )
            except (TypeError, ValueError):
                pass

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