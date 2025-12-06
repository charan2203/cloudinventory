from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/new/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('products/export/csv/', views.export_products_csv_view, name='product-export-csv'),

    # Supplier URLs
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/new/', views.SupplierCreateView.as_view(), name='supplier-create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier-update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier-delete'),

    # Stock movement URLs
    path('stock-movements/', views.StockMovementListView.as_view(), name='stockmovement-list'),
    path('stock-movements/new/', views.StockMovementCreateView.as_view(), name='stockmovement-create'),
    path('stock-movements/report/', views.stock_movement_report_view, name='stockmovement-report'),
]
