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
        'product_count'
    )
    list_display_links = ('indented_title',)
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('products')

    def product_count(self, instance):
        return instance.products.count()

    product_count.short_description = 'Товаров в категории'

class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    raw_id_fields = ('category',)

class ProductModelInline(admin.StackedInline):
    model = ProductModel
    extra = 0
    show_change_link = True
    fields = ('color', 'sku', 'price', 'is_active')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_price', 'is_active', 'created_at')
    list_filter = ('is_active', 'categories')
    search_fields = ('title', 'description', 'slug')
    inlines = [ProductCategoryInline, ProductModelInline]
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description')
        }),
        ('Цены и статус', {
            'fields': ('base_price', 'is_active')
        }),
    )

class ModelSizeInline(admin.TabularInline):
    model = ModelSize
    extra = 1
    min_num = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        return format_html('<img src="{}" height="100" />', obj.image.url) if obj.image else '-'
    image_preview.short_description = 'Превью'

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product_link', 'color', 'price', 'stock_sum', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('sku', 'product__title', 'color')
    inlines = [ModelSizeInline, ProductImageInline]
    autocomplete_fields = ['product']

    def product_link(self, obj):
        # Исправлено имя URL-шаблона
        url = reverse('admin:shop_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.title)
    product_link.short_description = 'Товар'

    def stock_sum(self, obj):
        return sum(obj.sizes.values_list('stock', flat=True))
    stock_sum.short_description = 'Общий остаток'

@admin.register(ModelSize)
class ModelSizeAdmin(admin.ModelAdmin):
    list_display = ('size', 'model_link', 'stock')
    search_fields = ('model__sku', 'size')

    def model_link(self, obj):
        # Исправлено имя URL
        url = reverse('admin:shop_productmodel_change', args=[obj.model.id])
        return format_html('<a href="{}">{}</a>', url, obj.model.sku)
    model_link.short_description = 'Модель'

admin.site.register(ProductImage)