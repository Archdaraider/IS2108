# auroramart_project/adminpanel/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# --- Choices for Customer Model ---

GENDER_CHOICES = [
    ('Female', 'Female'),
    ('Male', 'Male'),
]

EMPLOYMENT_CHOICES = [
    ('Full-time', 'Full-time'),
    ('Part-time', 'Part-time'),
    ('Self-employed', 'Self-employed'),
    ('Student', 'Student'),
    ('Retired', 'Retired'),
]

EDUCATION_CHOICES = [
    ('High School', 'High School'),
    ('Diploma', 'Diploma'),
    ('Bachelor', 'Bachelor'),
    ('Master', 'Master'),
    ('PhD', 'PhD'),
]

CATEGORY_CHOICES = [
    ('Electronics', 'Electronics'),
    ('Apparel', 'Apparel'),
    ('Home & Kitchen', 'Home & Kitchen'),
    ('Groceries', 'Groceries'),
    ('Books', 'Books'),
]

# --- Choices for Product Model (from b2c_products_500.csv) ---

PRODUCT_CATEGORY_CHOICES = [
    ('Automotive', 'Automotive'),
    ('Beauty & Personal Care', 'Beauty & Personal Care'),
    ('Books', 'Books'),
    ('Electronics', 'Electronics'),
    ('Fashion - Men', 'Fashion - Men'),
    ('Fashion - Women', 'Fashion - Women'),
    ('Groceries & Gourmet', 'Groceries & Gourmet'),
    ('Health', 'Health'),
    ('Home & Kitchen', 'Home & Kitchen'),
    ('Pet Supplies', 'Pet Supplies'),
    ('Sports & Outdoors', 'Sports & Outdoors'),
    ('Toys & Games', 'Toys & Games'),
]

PRODUCT_SUBCATEGORY_CHOICES = [
    ('Accessories', 'Accessories'),
    ('Action Figures', 'Action Figures'),
    ('Aquatic', 'Aquatic'),
    ('Bedding', 'Bedding'),
    ('Beverages', 'Beverages'),
    ('Board Games', 'Board Games'),
    ('Bottoms', 'Bottoms'),
    ('Breakfast', 'Breakfast'),
    ('Building Sets', 'Building Sets'),
    ('Cameras', 'Cameras'),
    ('Camping & Hiking', 'Camping & Hiking'),
    ('Car Care', 'Car Care'),
    ('Cat', 'Cat'),
    ('Children', 'Children'),
    ('Comics & Manga', 'Comics & Manga'),
    ('Cookware', 'Cookware'),
    ('Cycling', 'Cycling'),
    ('Dog', 'Dog'),
    ('Dresses', 'Dresses'),
    ('Exterior Accessories', 'Exterior Accessories'),
    ('Fiction', 'Fiction'),
    ('First Aid', 'First Aid'),
    ('Fitness Equipment', 'Fitness Equipment'),
    ('Footwear', 'Footwear'),
    ('Fragrances', 'Fragrances'),
    ('Grooming Tools', 'Grooming Tools'),
    ('Hair Care', 'Hair Care'),
    ('Handbags', 'Handbags'),
    ('Headphones', 'Headphones'),
    ('Health Foods', 'Health Foods'),
    ('Home Decor', 'Home Decor'),
    ('Interior Accessories', 'Interior Accessories'),
    ('Laptops', 'Laptops'),
    ('Makeup', 'Makeup'),
    ('Medical Devices', 'Medical Devices'),
    ('Monitors', 'Monitors'),
    ('Non?Fiction', 'Non-fiction'), # Corrected '?' from CSV
    ('Oils & Fluids', 'Oils & Fluids'),
    ('Outerwear', 'Outerwear'),
    ('Pantry Staples', 'Pantry Staples'),
    ('Personal Care', 'Personal Care'),
    ('Printers', 'Printers'),
    ('Puzzles', 'Puzzles'),
    ('STEM Toys', 'STEM Toys'),
    ('Skincare', 'Skincare'),
    ('Small Appliances', 'Small Appliances'),
    ('Small Pets', 'Small Pets'),
    ('Smart Home', 'Smart Home'),
    ('Smartphones', 'Smartphones'),
    ('Smartwatches', 'Smartwatches'),
    ('Snacks', 'Snacks'),
    ('Storage & Organization', 'Storage & Organization'),
    ('Supplements', 'Supplements'),
    ('Tablets', 'Tablets'),
    ('Team Sports', 'Team Sports'),
    ('Textbooks', 'Textbooks'),
    ('Tools & Equipment', 'Tools & Equipment'),
    ('Tops', 'Tops'),
    ('Vacuum & Cleaning', 'Vacuum & Cleaning'),
    ('Yoga & Wellness', 'Yoga & Wellness'),
]


# --- Core Business Models ---

class Customer(models.Model):
    """
    Extends Django's built-in User model to store AI-related profile data.
    """
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Fields for Customer Input (Onboarding) ---
    email = models.EmailField(unique=True, help_text="Used as the unique identifier and for login.")
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    
    # --- UPDATED with choices ---
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    employment_status = models.CharField(max_length=50, choices=EMPLOYMENT_CHOICES)
    occupation = models.CharField(max_length=50)
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    
    household_size = models.IntegerField()
    has_children = models.BooleanField()
    monthly_income_sgd = models.DecimalField(max_digits=10, decimal_places=2)
    
    # --- UPDATED with choices ---
    preferred_category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.email

    @property
    def cID(self):
        return f"CUST-{self.id:06d}"


class Product(models.Model):
    """
    Represents the Product Catalogue[cite: 43].
    Managed by the admin panel[cite: 63].
    """
    # Fields from "Product Catalogue (500 SKUs)" [cite: 43]
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # === UPDATED: Added 'choices' attribute ===
    category = models.CharField(max_length=100, choices=PRODUCT_CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, choices=PRODUCT_SUBCATEGORY_CHOICES)
    
    price = models.DecimalField(max_digits=10, decimal_places=2) # Renamed from unit_price
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    stock = models.IntegerField(verbose_name="Stock") # Renamed from quantity_on_hand
    reorder_threshold = models.IntegerField() # Renamed from reorder_quantity
    
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return f"{self.sku}: {self.name}"

class Order(models.Model):
    """
    Represents a customer's order (a "basket").
    """
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True, verbose_name="Order Placed At")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # --- NO CHANGE NEEDED: This field already uses choices ---
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    fulfillment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    shipping_address = models.TextField()

    def __str__(self):
        return f"Order {self.id} by {self.customer.email if self.customer else 'Guest'}"

    @property
    def oID(self):
        return f"ORD-{self.id:08d}"

class OrderItem(models.Model):
    """
    Represents a single product within an Order.
    This model links Products to Orders, creating the "basket".
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Unknown Product'}"

# --- AI/ML Feature Model ---

class DecisionTreeModel(models.Model):
    """
    Model to track the deployed ML model's metadata and performance[cite: 141].
    """
    model_name = models.CharField(max_length=255, default="DecisionTree_PreferredCategory")
    version = models.CharField(max_length=50, unique=True)
    training_date = models.DateTimeField(default=timezone.now)
    accuracy = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    file_path = models.CharField(max_length=255, help_text="Path to the deployed model file [cite: 135]")

    def __str__(self):
        return f"{self.model_name} v{self.version} ({'Active' if self.is_active else 'Inactive'})"
