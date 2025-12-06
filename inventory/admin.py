from django.contrib import admin
from .models import Category, Supplier, Product, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'supplier',
        'unit_price',
        'quantity_in_stock',
        'reorder_level',
        'is_low_stock',
    )
    list_filter = ('category', 'supplier')
    search_fields = ('name', 'sku')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'movement_date', 'created_at')
    list_filter = ('movement_type', 'movement_date')
    search_fields = ('product__name', 'product__sku')
