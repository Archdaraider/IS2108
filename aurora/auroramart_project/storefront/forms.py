# auroramart_project/storefront/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from adminpanel.models import Customer
from datetime import date

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
    # Define occupation choices
    OCCUPATION_CHOICES = [
        ('', 'Select occupation'),
        ('sales', 'Sales'),
        ('service', 'Service'),
        ('admin', 'Admin'),
        ('tech', 'Tech'),
        ('education', 'Education'),
        ('skilled_trades', 'Skilled Trades'),
    ]
    
    # Date of birth field (will be converted to age)
    # Calculate maximum date (14 years ago from today) and minimum date (100 years ago)
    from datetime import timedelta
    today = date.today()
    # Calculate 14 years ago, handling leap year edge cases
    try:
        max_date = date(today.year - 14, today.month, today.day)
    except ValueError:
        # Handle leap year edge case (e.g., Feb 29 doesn't exist in non-leap years)
        max_date = date(today.year - 14, today.month, 28)  # Use Feb 28 as fallback
    min_date = date(today.year - 100, 1, 1)
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': max_date.strftime('%Y-%m-%d'),  # Maximum date: 14 years ago (must be at least 14)
            'min': min_date.strftime('%Y-%m-%d'),  # Minimum date: 100 years ago
        }),
        label='Date of Birth',
        required=True,
        help_text='You must be at least 14 years old to register. Your age will be calculated from your date of birth.'
    )
    
    # Override occupation field to use dropdown with choices
    occupation = forms.ChoiceField(
        choices=OCCUPATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select occupation'
        }),
        required=True
    )
    
    class Meta:
        model = Customer
        fields = [
            'gender',
            'employment_status',
            'occupation',
            'education',
            'household_size',
            'has_children',
            'monthly_income_sgd',
        ]
        widgets = {
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select gender'
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select employment status'
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
            'monthly_income_sgd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 5000',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'has_children': 'Do you have children?',
            'monthly_income_sgd': 'Monthly income (SGD)',
            'household_size': 'Household size',
        }
    
    def clean_date_of_birth(self):
        """Validate that the user is at least 14 years old."""
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            if age < 14:
                raise forms.ValidationError(
                    'You must be at least 14 years old to register for an account.',
                    code='age_restriction'
                )
            
            # Also check maximum reasonable age (e.g., 120 years)
            if age > 120:
                raise forms.ValidationError(
                    'Please enter a valid date of birth.',
                    code='invalid_age'
                )
        
        return date_of_birth


class CheckoutForm(forms.Form):
    """Form for checkout process"""
    # Address selection
    saved_address_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    use_new_address = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )
    
    # New address fields (only required if use_new_address is True)
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        }),
        label='Full Name',
        required=False
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',
            'placeholder': 'e.g. +65 9123 4567'
        }),
        label='Phone Number',
        required=False
    )
    address = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street address'
        }),
        label='Address',
        required=False
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        }),
        label='City',
        required=False
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal code'
        }),
        label='Postal Code',
        required=False
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        }),
        label='Country',
        required=False
    )
    floor_unit_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. #12-34'
        }),
        label='Floor/Unit Number',
        required=False,
        help_text='Optional'
    )
    save_address = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Save this address for future use'
    )
    
    # Payment method selection
    saved_payment_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    use_new_payment = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('paynow', 'PayNow'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Payment Method',
        required=False
    )
    
    # Card details fields (only required if payment_method is 'card')
    card_type = forms.ChoiceField(
        choices=[
            ('visa', 'Visa'),
            ('mastercard', 'Mastercard'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Card Type',
        required=False
    )
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'maxlength': '19'
        }),
        label='Card Number',
        required=False
    )
    card_expiry = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'maxlength': '5'
        }),
        label='Expiry Date',
        required=False
    )
    card_cvv = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '3',
            'type': 'password'
        }),
        label='CVV',
        required=False
    )
    cardholder_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name on card'
        }),
        label='Cardholder Name',
        required=False
    )
    
    # Delivery time selection
    delivery_time = forms.ChoiceField(
        choices=[
            ('standard', 'Standard Delivery - Free (5-7 business days)'),
            ('express', 'Express Delivery - $4.99 (2-3 business days)'),
            ('overnight', 'Overnight Delivery - $12.99 (Next business day)'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Delivery Time',
        required=True,
        initial='standard'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check POST data directly for radio button selections
        saved_address_id_value = self.data.get('saved_address_id', '')
        saved_payment_id_value = self.data.get('saved_payment_id', '')
        use_new_address_value = self.data.get('use_new_address', '0')
        use_new_payment_value = self.data.get('use_new_payment', '0')
        payment_method = cleaned_data.get('payment_method') or self.data.get('payment_method', '')
        
        # Validate address - check if saved address is selected OR new address fields are filled
        has_saved_address = saved_address_id_value and saved_address_id_value != ''
        has_new_address_fields = any([
            self.data.get('full_name'),
            self.data.get('phone_number'),
            self.data.get('address'),
            self.data.get('city'),
            self.data.get('postal_code'),
            self.data.get('country')
        ])
        
        if has_saved_address:
            # A saved address was selected - no validation needed
            pass
        elif use_new_address_value == '1' or has_new_address_fields:
            # New address is being used - validate required fields
            if not cleaned_data.get('full_name'):
                self.add_error('full_name', 'Full name is required.')
            if not cleaned_data.get('phone_number'):
                self.add_error('phone_number', 'Phone number is required.')
            if not cleaned_data.get('address'):
                self.add_error('address', 'Address is required.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'City is required.')
            if not cleaned_data.get('postal_code'):
                self.add_error('postal_code', 'Postal code is required.')
            if not cleaned_data.get('country'):
                self.add_error('country', 'Country is required.')
        else:
            # Neither saved nor new address selected
            self.add_error(None, 'Please select an address or add a new one.')
        
        # Validate payment method - check if saved payment is selected OR new payment method is selected
        has_saved_payment = saved_payment_id_value and saved_payment_id_value != ''
        has_payment_method = payment_method and payment_method != ''
        
        if has_saved_payment:
            # A saved payment method was selected - no validation needed
            pass
        elif use_new_payment_value == '1' or has_payment_method:
            # New payment method is being used
            if not payment_method:
                self.add_error('payment_method', 'Payment method is required.')
            # If payment method is card, validate card fields
            if payment_method == 'card':
                card_type = cleaned_data.get('card_type') or self.data.get('card_type', '')
                card_number = (cleaned_data.get('card_number') or self.data.get('card_number', '')).strip()
                card_expiry = (cleaned_data.get('card_expiry') or self.data.get('card_expiry', '')).strip()
                card_cvv = (cleaned_data.get('card_cvv') or self.data.get('card_cvv', '')).strip()
                cardholder_name = (cleaned_data.get('cardholder_name') or self.data.get('cardholder_name', '')).strip()
                
                if not card_type:
                    self.add_error('card_type', 'Card type is required for card payments.')
                if not card_number:
                    self.add_error('card_number', 'Card number is required for card payments.')
                if not card_expiry:
                    self.add_error('card_expiry', 'Expiry date is required for card payments.')
                if not card_cvv:
                    self.add_error('card_cvv', 'CVV is required for card payments.')
                elif len(card_cvv) != 3:
                    self.add_error('card_cvv', 'CVV must be exactly 3 digits.')
                if not cardholder_name:
                    self.add_error('cardholder_name', 'Cardholder name is required for card payments.')
        else:
            # Neither saved nor new payment method selected
            self.add_error(None, 'Please select a payment method or add a new one.')
        
        return cleaned_data


class ProductReviewForm(forms.Form):
    """Form for submitting product reviews"""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True,
        min_value=1,
        max_value=5
    )
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a title for your review'
        }),
        label='Review Title',
        required=True
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Share your experience with this product...'
        }),
        label='Review Description',
        required=True
    )
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Upload Photo (Optional)',
        required=False,
        help_text='Upload a photo of the item you received'
    )
    is_anonymous = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Post as anonymous'
    )

class DeliveryServiceReviewForm(forms.Form):
    """Form for reviewing delivery service"""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True,
        min_value=1,
        max_value=5
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your experience with the delivery service...'
        }),
        label='Delivery Review (Optional)',
        required=False
    )
    is_anonymous = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Post as anonymous'
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


class AddressForm(forms.ModelForm):
    """Form for managing saved addresses"""
    class Meta:
        from .models import SavedAddress
        model = SavedAddress
        fields = ['full_name', 'phone_number', 'address', 'city', 'postal_code', 'country', 'floor_unit_number', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'tel',
                'placeholder': 'e.g. +65 9123 4567'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'floor_unit_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. #12-34 (Optional)'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'phone_number': 'Phone Number',
            'address': 'Address',
            'city': 'City',
            'postal_code': 'Postal Code',
            'country': 'Country',
            'floor_unit_number': 'Floor/Unit Number (Optional)',
            'is_default': 'Set as default address',
        }


class PaymentMethodForm(forms.ModelForm):
    """Form for managing saved payment methods"""
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'maxlength': '19'
        }),
        label='Card Number',
        help_text='Only last 4 digits will be saved for security'
    )
    card_expiry = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'maxlength': '5'
        }),
        label='Expiry Date',
    )
    card_cvv = forms.CharField(
        max_length=3,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '3',
            'type': 'password'
        }),
        label='CVV',
        help_text='Required for verification but not saved'
    )
    
    class Meta:
        from .models import SavedPaymentMethod
        model = SavedPaymentMethod
        fields = ['payment_type', 'cardholder_name', 'card_last_four', 'card_expiry', 'is_default']
        widgets = {
            'payment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cardholder_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name on card'
            }),
            'card_last_four': forms.HiddenInput(),
            'card_expiry': forms.HiddenInput(),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'payment_type': 'Payment Type',
            'cardholder_name': 'Cardholder Name',
            'is_default': 'Set as default payment method',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        card_number = cleaned_data.get('card_number', '').strip().replace(' ', '')
        card_expiry = cleaned_data.get('card_expiry', '').strip()
        card_cvv = cleaned_data.get('card_cvv', '').strip()
        
        if payment_type == 'card':
            if not card_number:
                self.add_error('card_number', 'Card number is required for card payments.')
            elif len(card_number) < 13:
                self.add_error('card_number', 'Card number must be at least 13 digits.')
            else:
                # Extract last 4 digits
                cleaned_data['card_last_four'] = card_number[-4:]
            
            if not card_expiry:
                self.add_error('card_expiry', 'Expiry date is required for card payments.')
            elif len(card_expiry) != 5 or card_expiry[2] != '/':
                self.add_error('card_expiry', 'Expiry date must be in MM/YY format.')
            
            if not card_cvv:
                self.add_error('card_cvv', 'CVV is required for card payments.')
            elif len(card_cvv) != 3:
                self.add_error('card_cvv', 'CVV must be exactly 3 digits.')
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile (User model fields)"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'username': 'Username',
        }