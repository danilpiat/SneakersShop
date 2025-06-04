import base64

import rest_framework.serializers
from rest_framework import serializers
from .models import *


class Base64ImageField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            return None

        try:
            with open(value.path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(source='parent.id', allow_null=True)
    level = serializers.IntegerField(source='get_level')  # Используем метод get_level из MPTT

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent_id', 'level', 'is_active')

class ModelImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    class Meta:
        model = ModelImage
        fields = ('image', 'is_main', 'order_index')


class ModelSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelSize
        fields = ('size', 'stock')


class ProductModelSerializer(serializers.ModelSerializer):
    sizes = ModelSizeSerializer(many=True)
    images = ModelImageSerializer(many=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'color', 'sku', 'price', 'sizes', 'images')

class BrandSerializer(serializers.ModelSerializer):
    logo = Base64ImageField()
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
        if obj.image:
            return Base64ImageField().to_representation(obj.image)

        main_model_image = ModelImage.objects.filter(
            model__product=obj,
            is_main=True
        ).first()

        if main_model_image:
            return ModelImageSerializer(main_model_image).data['image']

        first_image = ModelImage.objects.filter(
            model__product=obj
        ).first()

        return ModelImageSerializer(first_image).data['image'] if first_image else None

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