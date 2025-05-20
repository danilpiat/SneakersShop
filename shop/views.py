from django.db.models import Q
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

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                descendants = category.get_descendants(include_self=True)
                queryset = queryset.filter(
                    productcategory__category__in=descendants
                ).distinct()
            except Category.DoesNotExist:
                return queryset.none()

        return queryset.prefetch_related('models', 'models__sizes', 'models__images')

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        product = self.get_object()
        models = product.models.filter(is_active=True)
        serializer = ProductModelSerializer(models, many=True)
        return Response(serializer.data)