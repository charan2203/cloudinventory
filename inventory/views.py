from datetime import datetime

from django.db.models import Sum, F
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Product, Supplier, StockMovement
from .forms import ProductForm, SupplierForm, StockMovementForm
import csv


def dashboard_view(request):
    total_products = Product.objects.count()
    total_suppliers = Supplier.objects.count()

    total_stock_value = Product.objects.aggregate(
        total=Sum(F('unit_price') * F('quantity_in_stock'))
    )['total'] or 0

    low_stock_products = Product.objects.filter(
        quantity_in_stock__lt=F('reorder_level')
    )[:10]

    recent_movements = StockMovement.objects.select_related('product').all()[:5]

    context = {
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'total_stock_value': total_stock_value,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
    }
    return render(request, 'inventory/dashboard.html', context)


class ProductListView(ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'supplier')
        q = self.request.GET.get('q')
        low_stock = self.request.GET.get('low_stock')

        if q:
            queryset = queryset.filter(
                models.Q(name__icontains=q) | models.Q(sku__icontains=q)
            )
        if low_stock == '1':
            queryset = queryset.filter(quantity_in_stock__lt=F('reorder_level'))

        return queryset


class ProductDetailView(DetailView):
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product-list')


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('product-list')


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')


class SupplierListView(ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10


class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier-list')


class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier-list')


class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'inventory/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')


class StockMovementListView(ListView):
    model = StockMovement
    template_name = 'inventory/stockmovement_list.html'
    context_object_name = 'movements'
    paginate_by = 10

    def get_queryset(self):
        queryset = StockMovement.objects.select_related('product')
        product_id = self.request.GET.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class StockMovementCreateView(CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stockmovement_form.html'
    success_url = reverse_lazy('stockmovement-list')


def stock_movement_report_view(request):
    movements = StockMovement.objects.select_related('product').all()

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            movements = movements.filter(movement_date__date__gte=start_date)
        except ValueError:
            start_date = None

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            movements = movements.filter(movement_date__date__lte=end_date)
        except ValueError:
            end_date = None

    context = {
        'movements': movements,
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
    }
    return render(request, 'inventory/stockmovement_report.html', context)


def export_products_csv_view(request):
    """Non-CRUD feature: export product list as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'SKU', 'Category', 'Supplier', 'Unit Price', 'Quantity', 'Reorder Level'])

    products = Product.objects.select_related('category', 'supplier').all()

    for product in products:
        writer.writerow([
            product.name,
            product.sku,
            product.category.name if product.category else '',
            product.supplier.name if product.supplier else '',
            product.unit_price,
            product.quantity_in_stock,
            product.reorder_level,
        ])

    return response
