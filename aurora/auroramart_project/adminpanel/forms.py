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
    # Add username and password fields for User creation
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Confirm Password",
        help_text="Enter the same password as before, for verification."
    )
    
    class Meta:
        model = Customer
        exclude = ('user', 'preferred_category',)
        # Add a help text for the boolean field
        help_texts = {
            'has_children': 'Check this box if the customer has children.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing customer, make password optional
        if self.instance and self.instance.pk:
            self.fields['username'].required = False
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False
            self.fields['username'].help_text = "Leave blank to keep existing username."
            self.fields['password'].help_text = "Leave blank to keep existing password."
            
            # Pre-fill username if user exists
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Only validate if username is provided
        if username:
            # Check if user already exists (exclude current user when editing)
            existing_user = User.objects.filter(username=username)
            if self.instance and self.instance.user:
                existing_user = existing_user.exclude(pk=self.instance.user.pk)
            
            if existing_user.exists():
                raise forms.ValidationError("A user with that username already exists.")
        return username
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        # Only validate if password is provided
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("The two password fields didn't match.")
            
            # Validate password strength
            if password:
                try:
                    validate_password(password)
                except forms.ValidationError as e:
                    raise forms.ValidationError(list(e.messages))
        
        return password_confirm

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
        # Ensure products are properly loaded and displayed
        self.fields['product'].queryset = Product.objects.all().order_by('name')
        self.fields['product'].required = False
        self.fields['product'].empty_label = "Select a product..."
        
        self.fields['quantity'].required = False
        self.fields['quantity'].initial = 1
        # Optional: set a default min_value for quantity
        self.fields['quantity'].widget.attrs.update({'min': '1', 'value': '1'})
        
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        
        # If product is provided, ensure quantity is set
        if product:
            if not quantity or quantity == '':
                cleaned_data['quantity'] = 1
            else:
                quantity = int(quantity) if isinstance(quantity, str) else quantity
                if quantity <= 0:
                    raise forms.ValidationError("Quantity must be greater than 0.")
                cleaned_data['quantity'] = quantity
        
        # If quantity is provided but no product, that's invalid
        if quantity and not product:
            raise forms.ValidationError("Please select a product.")
            
        return cleaned_data
    
    def has_changed(self):
        """Override to ensure forms with product selected are considered changed"""
        # If product is selected, consider the form as changed even if quantity is default
        if self.cleaned_data and self.cleaned_data.get('product'):
            return True
        return super().has_changed()
        
# Create formset factory with 0 extra empty forms (we'll add dynamically with JS)
OrderItemFormSet = inlineformset_factory(
    Order,              # parent model
    OrderItem,          # child model
    form=OrderItemForm, # form to use for each child
    can_delete=True,   
    min_num=1,          # Require at least 1 item
    extra=0,            # No extra empty forms by default (add with button)
    validate_min=False,  # Don't validate minimum - we handle this manually
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

