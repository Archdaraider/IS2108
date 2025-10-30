# adminpanel/forms.py
from django import forms
from .models import Customer, Product, Order

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        # === UPDATED ===
        # 'preferred_category' is now included in the form
        fields = [
            'email', 'name', 'age', 'gender', 'employment_status', 
            'occupation', 'education', 'household_size', 
            'has_children', 'monthly_income_sgd', 'preferred_category'
        ]

class ProductForm(forms.ModelForm):
    # ... (This form remains the same) ...
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'description', 'category', 'subcategory', 
            'price', 'rating', 'stock', 'reorder_threshold', 'image'
        ]

class OrderForm(forms.ModelForm):
    # ... (This form remains the same) ...
    class Meta:
        model = Order
        fields = [
            'customer', 
            'shipping_address',
            'fulfillment_status',
            'total_amount',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
        }