from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.sku})'

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_in_stock < self.reorder_level


class StockMovement(models.Model):
    MOVEMENT_IN = 'IN'
    MOVEMENT_OUT = 'OUT'
    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, 'Stock In'),
        (MOVEMENT_OUT, 'Stock Out'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
    )
    movement_type = models.CharField(
        max_length=3,
        choices=MOVEMENT_CHOICES,
    )
    quantity = models.PositiveIntegerField()
    movement_date = models.DateTimeField(default=timezone.now)
    reference_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self) -> str:
        return f'{self.movement_type} {self.quantity} of {self.product}'

    def clean(self) -> None:
        """Business validation to prevent negative stock."""
        if self.quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')

        if self.movement_type == self.MOVEMENT_OUT:
            current_stock = self.product.quantity_in_stock
            if self.pk:
                # On update, add back previous quantity first to avoid double counting
                previous = StockMovement.objects.get(pk=self.pk)
                if previous.movement_type == self.MOVEMENT_OUT:
                    current_stock += previous.quantity
                elif previous.movement_type == self.MOVEMENT_IN:
                    current_stock -= previous.quantity

            if self.quantity > current_stock:
                raise ValidationError(
                    f'Not enough stock to move out {self.quantity} units. '
                    f'Current stock is {current_stock}.'
                )

    def save(self, *args, **kwargs):
        """
        Override save to update product.stock appropriately.
        Handles both create and update in a safe way.
        """
        self.full_clean()  # run clean() before saving

        is_new = self.pk is None
        if not is_new:
            # Revert previous movement effect
            previous = StockMovement.objects.get(pk=self.pk)
            product = previous.product

            if previous.movement_type == self.MOVEMENT_IN:
                product.quantity_in_stock -= previous.quantity
            else:  # OUT
                product.quantity_in_stock += previous.quantity
            product.save()

        super().save(*args, **kwargs)

        # Apply new movement effect
        product = self.product
        if self.movement_type == self.MOVEMENT_IN:
            product.quantity_in_stock += self.quantity
        else:
            product.quantity_in_stock -= self.quantity
        product.save()
