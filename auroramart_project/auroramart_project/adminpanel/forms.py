from django import forms
from .models import Customer, Product, Order, OrderItem
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password 

class BaseForm(forms.ModelForm):
    """
    A base form to add the 'error-field' class to widgets
    of fields that have errors.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Loop through all fields in the form
        for field_name, field in self.fields.items():
            if self.has_error(field_name):
                current_classes = field.widget.attrs.get('class', '')

                if 'error-field' not in current_classes:
                    field.widget.attrs['class'] = (current_classes + ' error-field').strip()

class CustomerForm(BaseForm):
    class Meta:
        model = Customer
        exclude = ('user', 'preferred_category',)
        # Add a help text for the boolean field
        help_texts = {
            'has_children': 'Check this box if the customer has children.',
        }

class ProductForm(BaseForm):
    class Meta:
        model = Product
        fields = '__all__' # Include all fields from the Product model
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'sku': 'e.g HKHD-ZBIKCIDK',
        }

class OrderForm(BaseForm):
    class Meta:
        model = Order
        exclude = ('total_amount',) # <-- UPDATED
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 4}),
        }

class OrderItemForm(BaseForm):
    class Meta:
        model = OrderItem
        fields = ('product', 'quantity') # User will only fill these two

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].required = False
        self.fields['quantity'].required = False
        # Optional: set a default min_value for quantity
        self.fields['quantity'].widget.attrs.update({'min': '1'})
        
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        
        # If both product and quantity are provided, validate
        if product and quantity:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than 0.")
        
        # If product is provided but quantity is not, set default quantity
        if product and not quantity:
            cleaned_data['quantity'] = 1
            
        return cleaned_data
        
# Create formset factory with 1 extra empty form for adding new items
OrderItemFormSet = inlineformset_factory(
    Order,              # parent model
    OrderItem,          # child model
    form=OrderItemForm, # form to use for each child
    can_delete=True,   
    min_num=0,   
    extra=1,            # Show 1 empty form for adding new items
    validate_min=False,  # Don't require minimum forms
)

# --- Admin User Management Forms ---

class AdminUserForm(BaseForm):
    """
    Form for creating new admin users (staff users, not superusers).
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = forms.EmailField(required=True)
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        min_length=1,
        help_text="Password for the admin user."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        min_length=1,
        help_text="Enter the same password as before, for verification."
    )
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if user already exists (for create, not update)
        if not self.instance.pk and User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already exists (for create, not update)
        if not self.instance.pk and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("The two password fields didn't match.")
        
        # Validate password strength
        if password:
            try:
                validate_password(password)
            except forms.ValidationError as e:
                raise forms.ValidationError(list(e.messages))
        
        return password_confirm
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set the password properly (hashed)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        # Set staff status (not superuser)
        user.is_staff = True
        user.is_superuser = False
        
        if commit:
            user.save()
        return user

