from django.contrib import admin
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import *

class ModelSizeInline(admin.TabularInline):
    model = ModelSize
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'color', 'price', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('sku', 'product__title')
    inlines = [ModelSizeInline, ProductImageInline]

class ProductModelInline(admin.TabularInline):
    model = ProductModel
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_price', 'is_active')
    list_filter = ('is_active', 'categories')
    search_fields = ('title', 'description')
    filter_horizontal = ('categories',)
    inlines = [ProductModelInline]

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'is_active')
    list_display_links = ('indented_title',)
    list_filter = ('is_active',)
    search_fields = ('name',)