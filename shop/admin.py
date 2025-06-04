# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from mptt.admin import DraggableMPTTAdmin

from .models import *
from admin_auto_filters.filters import AutocompleteFilter

class ProductFilter(AutocompleteFilter):
    title = 'Товар'
    field_name = 'product'

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = (
        'tree_actions',
        'indented_title',
        'slug',
        'is_active',
        'product_count',
        'image_preview'  # Добавлено превью изображения
    )
    list_display_links = ('indented_title',)
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    fields = ('name', 'slug', 'parent', 'is_active', 'image')
    readonly_fields = ('image_preview',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('products')

    def product_count(self, instance):
        return instance.products.count()

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "-"

    image_preview.short_description = "Превью"

    product_count.short_description = 'Товаров в категории'

class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    raw_id_fields = ('category',)

class ProductModelInline(admin.StackedInline):
    model = ProductModel
    extra = 0
    show_change_link = True
    fields = ('color', 'sku', 'is_active')

class ModelImageInline(admin.TabularInline):  # Переименовали ProductImageInline в ModelImageInline
    model = ModelImage  # Изменили модель
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        return format_html('<img src="{}" height="100" />', obj.image.url) if obj.image else '-'
    image_preview.short_description = 'Превью'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_price', 'is_active', 'created_at', 'image_preview')
    list_filter = ('is_active', 'categories', 'brand')
    search_fields = ('title', 'description', 'slug')
    inlines = [ProductCategoryInline, ProductModelInline]
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('image_preview',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'brand', 'image')  # Добавили поле image
        }),
        ('Цены и статус', {
            'fields': ('base_price', 'is_active')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = "Превью изображения"

class ModelSizeInline(admin.TabularInline):
    model = ModelSize
    extra = 1
    min_num = 1
    fields = ('size', 'price', 'stock')  # Добавляем поле price

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'logo_preview')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('logo_preview',)
    list_filter = ('is_active',)

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" height="50" />', obj.logo.url)
        return "-"
    logo_preview.short_description = "Превью логотипа"

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product_link', 'color', 'min_price', 'max_price', 'stock_sum', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('sku', 'product__title', 'color')
    inlines = [ModelSizeInline, ModelImageInline]  # Используем новый ModelImageInline
    autocomplete_fields = ['product']

    def product_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.title)
    product_link.short_description = 'Товар'

    def stock_sum(self, obj):
        return sum(obj.sizes.values_list('stock', flat=True))
    stock_sum.short_description = 'Общий остаток'

    def min_price(self, obj):
        return obj.min_price
    min_price.short_description = 'Мин. цена'

    def max_price(self, obj):
        return obj.max_price
    max_price.short_description = 'Макс. цена'

@admin.register(ModelSize)
class ModelSizeAdmin(admin.ModelAdmin):
    list_display = ('size', 'model_link', 'stock')
    search_fields = ('model__sku', 'size')

    def model_link(self, obj):
        url = reverse('admin:shop_productmodel_change', args=[obj.model.id])
        return format_html('<a href="{}">{}</a>', url, obj.model.sku)
    model_link.short_description = 'Модель'

# Изменили регистрацию модели
admin.site.register(ModelImage)