# models.py
from django.db import models
from django.contrib.auth.models import User
from adminpanel.models import Product, Customer, Order

# --- Shopping Cart Models ---

class Cart(models.Model):
    """Shopping cart for a user session or logged-in user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart {self.session_key}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    """Individual item in a shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

    class Meta:
        unique_together = ['cart', 'product']

# --- Wishlist Models ---

class Wishlist(models.Model):
    """User's wishlist/favorites."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

class WishlistItem(models.Model):
    """Individual item in a wishlist."""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"

    class Meta:
        unique_together = ['wishlist', 'product']

# --- Product Review Models ---

class ProductReview(models.Model):
    """Customer reviews for products."""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"
    
    @property
    def helpful_count(self):
        """Get count of users who found this review helpful."""
        return self.helpful_votes.filter(is_helpful=True).count()
    
    def get_masked_username(self):
        """Return masked username like 'h***n'."""
        username = self.user.username
        if len(username) <= 2:
            return username[0] + '*' * (len(username) - 1)
        return username[0] + '*' * (len(username) - 2) + username[-1]

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

class ReviewImage(models.Model):
    """Images attached to product reviews."""
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for review {self.review.id}"

class ReviewHelpfulVote(models.Model):
    """Track which users found a review helpful."""
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['review', 'user']

class ReviewReport(models.Model):
    """Report abuse for reviews."""
    REPORT_REASONS = [
        ('abusive_language', 'Abusive Language'),
        ('incorrect_info', 'Incorrect information'),
        ('personal_details', 'Personal/order details'),
        ('prohibited_content', 'Prohibited Content'),
        ('external_link', 'External Link'),
        ('wrong_translation', 'Wrong Translation'),
        ('general_rejection', 'General rejection'),
    ]
    
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    additional_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = ['review', 'user']

# --- Delivery Service Review Model ---

class DeliveryServiceReview(models.Model):
    """Customer reviews for delivery service."""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey('adminpanel.Order', on_delete=models.CASCADE, related_name='delivery_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Order {self.order.id} ({self.rating} stars)"

    class Meta:
        unique_together = ['user', 'order']
        ordering = ['-created_at']

# --- Category Models for Storefront ---

class Category(models.Model):
    """Product categories for the storefront navigation."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class SubCategory(models.Model):
    """Subcategories for more detailed product organization."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        unique_together = ['category', 'slug']
        verbose_name_plural = "Subcategories"

# --- Banner/Promotion Models ---

class Banner(models.Model):
    """Homepage banners and promotions."""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/')
    link_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['display_order', 'created_at']

# --- Newsletter Subscription ---

class NewsletterSubscription(models.Model):
    """Email newsletter subscriptions."""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-subscribed_at']

# --- Saved Address and Payment Method Models ---

class SavedAddress(models.Model):
    """Saved shipping addresses for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    floor_unit_number = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.address}, {self.city}"

    def get_formatted_address(self):
        """Return formatted address string."""
        floor_unit = f", {self.floor_unit_number}" if self.floor_unit_number else ""
        return (
            f"{self.full_name}\n"
            f"{self.phone_number}\n"
            f"{self.address}{floor_unit}\n"
            f"{self.city}, {self.postal_code}\n"
            f"{self.country}"
        )

    class Meta:
        ordering = ['-is_default', '-created_at']

class SavedPaymentMethod(models.Model):
    """Saved payment methods for users."""
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('paynow', 'PayNow'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    
    # Card details (only for card payment type)
    cardholder_name = models.CharField(max_length=255, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)  # Last 4 digits only
    card_expiry = models.CharField(max_length=5, blank=True)  # MM/YY format
    
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.payment_type == 'card' and self.card_last_four:
            return f"Card ending in {self.card_last_four}"
        return self.get_payment_type_display()

    class Meta:
        ordering = ['-is_default', '-created_at']