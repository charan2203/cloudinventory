from django import forms
from .models import Product, Supplier, StockMovement


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'description',
            'category',
            'supplier',
            'unit_price',
            'quantity_in_stock',
            'reorder_level',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price is not None and unit_price <= 0:
            raise forms.ValidationError('Unit price must be greater than zero.')
        return unit_price

    def clean_reorder_level(self):
        reorder_level = self.cleaned_data.get('reorder_level')
        if reorder_level is not None and reorder_level < 0:
            raise forms.ValidationError('Reorder level cannot be negative.')
        return reorder_level


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'movement_type', 'quantity', 'movement_date', 'reference_note']
        widgets = {
            'movement_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # support initial datetime-local format
        if self.instance and self.instance.pk and self.instance.movement_date:
            self.initial['movement_date'] = self.instance.movement_date.strftime('%Y-%m-%dT%H:%M')

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        movement_type = cleaned_data.get('movement_type')
        quantity = cleaned_data.get('quantity')

        if product and movement_type == StockMovement.MOVEMENT_OUT and quantity:
            current_stock = product.quantity_in_stock

            # If updating existing movement, add back previous to current
            if self.instance and self.instance.pk:
                previous = StockMovement.objects.get(pk=self.instance.pk)
                if previous.movement_type == StockMovement.MOVEMENT_OUT:
                    current_stock += previous.quantity
                elif previous.movement_type == StockMovement.MOVEMENT_IN:
                    current_stock -= previous.quantity

            if quantity > current_stock:
                raise forms.ValidationError(
                    f'Cannot move out {quantity} units. '
                    f'Current available stock is {current_stock}.'
                )
        return cleaned_data
