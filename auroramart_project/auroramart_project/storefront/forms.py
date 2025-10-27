# auroramart_project/storefront/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from adminpanel.models import Customer

class UserRegistrationForm(UserCreationForm):
    """Form for user account creation"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })


class CustomerProfileForm(forms.ModelForm):
    """Form for customer profile creation and editing"""
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'placeholder': 'DD/MM/YYYY',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Customer
        fields = [
            'age',
            'gender',
            'employment_status',
            'occupation',
            'education',
            'household_size',
            'has_children',
            'monthly_income_sgd',
            'preferred_category'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age',
                'min': 1,
                'max': 120
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select gender'
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select employment status'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Occupation'
            }),
            'education': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select education level'
            }),
            'household_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5',
                'min': 1
            }),
            'has_children': forms.Select(
                choices=[(True, 'Yes'), (False, 'No')],
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Select'
                }
            ),
            'monthly_income_sgd': forms.Select(
                choices=[
                    ('', 'Select income range'),
                    ('0-2000', '$0 - $2,000'),
                    ('2001-4000', '$2,001 - $4,000'),
                    ('4001-6000', '$4,001 - $6,000'),
                    ('6001-8000', '$6,001 - $8,000'),
                    ('8001-10000', '$8,001 - $10,000'),
                    ('10001+', '$10,001+'),
                ],
                attrs={
                    'class': 'form-control'
                }
            ),
            'preferred_category': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'has_children': 'Do you have children?',
            'monthly_income_sgd': 'Monthly income (SGD)',
            'household_size': 'Household size',
            'preferred_category': 'Preferred shopping category'
        }


class CheckoutForm(forms.Form):
    """Form for checkout process"""
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your full shipping address'
        }),
        label='Shipping Address'
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('paypal', 'PayPal'),
            ('bank', 'Bank Transfer'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Payment Method'
    )


class ProductSearchForm(forms.Form):
    """Form for product search"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search product'
        })
    )