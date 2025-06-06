# models.py
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db.models.aggregates import Min, Max
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    image = models.ImageField(
        upload_to='category_images/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    def get_level(self):
        return self.level  # Свойство level предоставляется MPTTModel

    class MPTTMeta:
        order_insertion_by = ['name']
        level_attr = 'level'

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Brand(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to='brand_logos/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        related_name='products',  # Добавляем related_name
        blank=True
    )

    image = models.ImageField(  # Добавляем новое поле image
        upload_to='product_images/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ProductCategory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('product', 'category')


class ProductModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='models'
    )
    color = models.CharField(max_length=50)
    sku = models.CharField(
        max_length=50,
        unique=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.title} - {self.color}"

    @property
    def min_price(self):
        return self.sizes.aggregate(min_price=Min('price'))['min_price'] or 0

    # Добавляем свойство для получения максимальной цены модели
    @property
    def max_price(self):
        return self.sizes.aggregate(max_price=Max('price'))['max_price'] or 0


class ModelSize(models.Model):
    model = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name='sizes'
    )
    size = models.DecimalField(
        max_digits=4,
        decimal_places=1
    )
    price = models.DecimalField(  # Добавляем поле цены для каждого размера
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('model', 'size')

    def __str__(self):
        return f"Size {self.size} - {self.model}"


class ModelImage(models.Model):  # Переименовали ProductImage в ModelImage
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    model = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='product_images/'
    )
    is_main = models.BooleanField(default=False)
    order_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"Image for {self.model}"