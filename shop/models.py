# models.py
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator


class Category(models.Model):
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
    lft = models.IntegerField()
    rgt = models.IntegerField()
    depth = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"

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
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        through='ProductCategory'
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
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.title} - {self.color}"


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
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('model', 'size')

    def __str__(self):
        return f"Size {self.size} - {self.model}"


class ProductImage(models.Model):
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