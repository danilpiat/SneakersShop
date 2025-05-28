import rest_framework.serializers
from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(source='parent.id', allow_null=True)
    level = serializers.IntegerField(source='get_level')  # Используем метод get_level из MPTT

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent_id', 'level', 'is_active')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('image', 'is_main', 'order_index')


class ModelSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelSize
        fields = ('size', 'stock')


class ProductModelSerializer(serializers.ModelSerializer):
    sizes = ModelSizeSerializer(many=True)
    images = ProductImageSerializer(many=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'color', 'sku', 'price', 'sizes', 'images')

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'logo')

class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    categories = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='slug'
    )

    brand = BrandSerializer(read_only=True)
    available_sizes = serializers.SerializerMethodField()  # Добавляем доступные размеры

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'base_price', 'categories', 'main_image', 'brand', 'available_sizes')

    def get_main_image(self, obj):
        main_image = obj.models.filter(images__is_main=True).first()
        if main_image:
            return ProductImageSerializer(main_image.images.first()).data
        return None

    def get_available_sizes(self, obj):
        sizes = set()
        for product_model in obj.models.all():
            for size in product_model.sizes.all():
                sizes.add(size.size)
        return sorted(list(sizes))


class ProductDetailSerializer(ProductListSerializer):
    models = ProductModelSerializer(many=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ('description', 'models')