from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

from adminpanel.models import Product, Customer, OrderItem
from .models import Cart, CartItem, Wishlist, WishlistItem, ProductReview, Category, SubCategory, Banner, NewsletterSubscription
from .recommendations import get_recommendations, get_category_recommendations
from .forms import CustomerProfileForm
from .cart_helpers import get_or_create_cart, add_product_to_cart, update_cart_item_quantity

# --- Utility Functions ---

def get_cart_context(request):
    """Get cart context for templates."""
    cart = get_or_create_cart(request)
    return {
        'cart': cart,
        'cart_total_items': cart.total_items,
    }

def get_or_create_wishlist(request):
    """Get or create a wishlist for the current user."""
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        return wishlist
    return None

# --- Main Storefront Views ---

def homepage(request):
    """Homepage with featured products and banners."""
    # Get featured products (you can customize this logic)
    featured_products = Product.objects.filter(stock__gt=0).order_by('-rating')[:8]
    best_sellers = Product.objects.filter(stock__gt=0).order_by('-rating')[:8]
    
    # Get banners
    banners = Banner.objects.filter(is_active=True).order_by('display_order')
    
    # Get categories for navigation
    categories = Category.objects.filter(is_active=True)
    
    # Get cart context
    cart_context = get_cart_context(request)
    cart = cart_context['cart']
    cart_product_ids = set(cart.items.values_list('product_id', flat=True))
    
    context = {
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'banners': banners,
        'categories': categories,
        'cart_product_ids': cart_product_ids,
        'cart': cart,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/homepage.html', context)

def product_list(request, category_slug=None, subcategory_slug=None):
    """Product listing page with filtering and search."""
    products = Product.objects.filter(stock__gt=0)
    
    # Map category slugs to actual category names from PRODUCT_CATEGORY_CHOICES
    category_map = {
        'electronics': 'Electronics',
        'fashion-men': 'Fashion - Men',
        'fashion-women': 'Fashion - Women',
        'home-kitchen': 'Home & Kitchen',
        'beauty-personal-care': 'Beauty & Personal Care',
        'books': 'Books',
        'groceries-gourmet': 'Groceries & Gourmet',
        'health': 'Health',
        'sports-outdoors': 'Sports & Outdoors',
        'toys-games': 'Toys & Games',
        'automotive': 'Automotive',
        'pet-supplies': 'Pet Supplies',
    }
    
    category = None
    subcategory = None
    
    # Filter by category
    if category_slug:
        category_name = category_map.get(category_slug)
        if category_name:
            products = products.filter(category=category_name)
            category = {'name': category_name, 'slug': category_slug}
        
        # Filter by subcategory if provided
        if subcategory_slug:
            products = products.filter(subcategory__iexact=subcategory_slug.replace('-', ' '))
            subcategory = {'name': subcategory_slug.replace('-', ' ').title(), 'slug': subcategory_slug}
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(subcategory__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', 'best_match')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    else:  # best_match
        products = products.order_by('-rating', '-id')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all available product categories for sidebar
    from adminpanel.models import PRODUCT_CATEGORY_CHOICES
    categories = []
    for code, name in PRODUCT_CATEGORY_CHOICES:
        slug = name.lower().replace(' ', '-').replace('&', '').replace('--', '-')
        # Handle special cases
        if name == 'Fashion - Men':
            slug = 'fashion-men'
        elif name == 'Fashion - Women':
            slug = 'fashion-women'
        elif name == 'Beauty & Personal Care':
            slug = 'beauty-personal-care'
        elif name == 'Groceries & Gourmet':
            slug = 'groceries-gourmet'
        elif name == 'Sports & Outdoors':
            slug = 'sports-outdoors'
        elif name == 'Toys & Games':
            slug = 'toys-games'
        elif name == 'Pet Supplies':
            slug = 'pet-supplies'
        categories.append({'name': name, 'slug': slug})
    
    # Get cart to check which products are already in cart
    cart = get_or_create_cart(request)
    cart_product_ids = set(cart.items.values_list('product_id', flat=True))
    
    # Get wishlist product IDs for logged-in users
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    # Get "Next best action" recommendations using association rules
    next_best_products = []
    if category:
        try:
            next_best_products = get_category_recommendations(
                category_name, 
                exclude_skus=list(products[:5].values_list('sku', flat=True)),
                top_n=8
            )
        except Exception as e:
            # Fallback to popular products in category
            next_best_products = Product.objects.filter(
                category=category_name,
                stock__gt=0
            ).exclude(id__in=products[:5].values_list('id', flat=True)).order_by('-rating')[:8]
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'products': page_obj,
        'category': category,
        'subcategory': subcategory,
        'categories': categories,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
        'next_best_products': next_best_products,
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
        'cart': cart,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page."""
    product = get_object_or_404(Product, id=product_id)
    
    # Get reviews
    reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
    reviews_count = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or product.rating
    total_sold = product.total_sold
    favorites_count = product.favorites_count
    
    # Check if product is in cart
    cart = get_or_create_cart(request)
    cart_item = cart.items.filter(product=product).first()
    in_cart = cart_item is not None
    cart_quantity = cart_item.quantity if cart_item else 0
    cart_item_id = cart_item.id if cart_item else None
    
    # Check if product is in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            in_wishlist = wishlist.items.filter(product=product).exists()
    
    # Get frequently bought together using association rules
    try:
        frequently_bought = get_recommendations([product.sku], top_n=5)
        if not frequently_bought:
            frequently_bought = Product.objects.filter(
                category=product.category,
                stock__gt=0
            ).exclude(id=product.id)[:5]
    except:
        frequently_bought = Product.objects.filter(
            category=product.category,
            stock__gt=0
        ).exclude(id=product.id)[:5]
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        stock__gt=0
    ).exclude(id=product.id)[:4]
    
    # Get all product images (for slider) - if multiple images exist
    product_images = []
    if product.image:
        product_images.append(product.image)
    # You can add more images here if you have multiple images per product
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'product': product,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'avg_rating': float(avg_rating),
        'total_sold': total_sold,
        'favorites_count': favorites_count,
        'related_products': related_products,
        'frequently_bought': frequently_bought,
        'product_images': product_images,
        'in_cart': in_cart,
        'cart_quantity': cart_quantity,
        'cart_item_id': cart_item_id,
        'in_wishlist': in_wishlist,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/product_detail.html', context)

def shopping_cart(request):
    """Shopping cart page."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/shopping_cart.html', context)

@login_required
def wishlist(request):
    """User's wishlist page."""
    wishlist = get_or_create_wishlist(request)
    if wishlist:
        wishlist_items = wishlist.items.all()
    else:
        wishlist_items = []
    
    # Get cart context to check if wishlist items are in cart
    cart = get_or_create_cart(request)
    cart_product_ids = list(cart.items.values_list('product_id', flat=True))
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'wishlist_items': wishlist_items,
        'cart': cart,
        'cart_product_ids': cart_product_ids,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/wishlist.html', context)

# --- AJAX Views for Cart Operations ---

def get_cart_count(request):
    """Get current cart count via AJAX."""
    cart = get_or_create_cart(request)
    return JsonResponse({
        'success': True,
        'cart_total': cart.total_items,
        'cart_price': float(cart.total_price)
    })

@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        cart = get_or_create_cart(request)
        success, message, cart_item, cart_total = add_product_to_cart(cart, product_id, quantity)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total': cart_total,
                'cart_price': float(cart.total_price),
                'cart_item_id': cart_item.id if cart_item else None,
                'quantity': cart_item.quantity if cart_item else quantity
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding item to cart'
        })

@require_POST
def update_cart_item(request):
    """Update cart item quantity via AJAX."""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        # Support both cart item ID and product ID
        if item_id:
            cart_item = get_object_or_404(CartItem, id=item_id)
        elif product_id:
            cart = get_or_create_cart(request)
            cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
            if not cart_item:
                return JsonResponse({
                    'success': False,
                    'message': 'Item not found in cart'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Item ID or Product ID required'
            })
        
        # Use helper function
        success, removed, updated_cart_item, cart_total = update_cart_item_quantity(cart_item, quantity)
        
        if success:
            if removed:
                return JsonResponse({
                    'success': True,
                    'removed': True,
                    'cart_total': cart_total,
                    'cart_price': float(cart_item.cart.total_price)
                })
            else:
                return JsonResponse({
                    'success': True,
                    'cart_total': cart_total,
                    'cart_price': float(updated_cart_item.cart.total_price),
                    'item_total': float(updated_cart_item.total_price),
                    'quantity': updated_cart_item.quantity
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error updating cart item'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating cart item'
        })

@require_POST
def remove_from_cart(request):
    """Remove item from cart via AJAX."""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error removing item from cart'
        })

# --- Wishlist AJAX Views ---

@login_required
@require_POST
def add_to_wishlist(request):
    """Toggle product in wishlist via AJAX (add if not present, remove if present)."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request)
        
        if wishlist:
            wishlist_item = WishlistItem.objects.filter(
                wishlist=wishlist,
                product=product
            ).first()
            
            if wishlist_item:
                # Item exists, remove it
                wishlist_item.delete()
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} removed from wishlist',
                    'in_wishlist': False
                })
            else:
                # Item doesn't exist, add it
                WishlistItem.objects.create(
                    wishlist=wishlist,
                    product=product
                )
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} added to wishlist',
                    'in_wishlist': True
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to use wishlist'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating wishlist'
        })

@login_required
@require_POST
def remove_from_wishlist(request):
    """Remove item from wishlist via AJAX."""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        wishlist_item = get_object_or_404(WishlistItem, id=item_id)
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from wishlist'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error removing item from wishlist'
        })

# --- Authentication Views ---

def login_view(request):
    """Customer login page with email support."""
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        email_or_username = request.POST.get('username')  # Can be email or username
        password = request.POST.get('password')
        
        # Try to authenticate with email first, then username
        user = None
        if '@' in email_or_username:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(request, username=email_or_username, password=password)
        
        if user:
            # Merge session cart with user cart on login
            session_key = request.session.session_key
            if session_key:
                session_cart = Cart.objects.filter(session_key=session_key).first()
                if session_cart and session_cart.items.exists():
                    # Get or create user cart
                    user_cart, created = Cart.objects.get_or_create(user=user, defaults={'session_key': None})
                    
                    # Merge items from session cart to user cart
                    for session_item in session_cart.items.all():
                        user_item, item_created = CartItem.objects.get_or_create(
                            cart=user_cart,
                            product=session_item.product,
                            defaults={'quantity': session_item.quantity}
                        )
                        if not item_created:
                            # Item already exists in user cart, merge quantities
                            user_item.quantity += session_item.quantity
                            if user_item.quantity > user_item.product.stock:
                                user_item.quantity = user_item.product.stock
                            user_item.save()
                    
                    # Delete session cart after merging
                    session_cart.delete()
            
            login(request, user)
            next_url = request.GET.get('next', 'homepage')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email/username or password')
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    # Always show Google OAuth (even if credentials not configured, button will show)
    try:
        import social_django
        context = {
            'SOCIAL_AUTH_ENABLED': True,  # Always True if social_django is installed
            **cart_context,  # Add cart info to context
        }
    except ImportError:
        context = {
            'SOCIAL_AUTH_ENABLED': False,
            **cart_context,  # Add cart info to context
        }
    return render(request, 'storefront/login.html', context)

def register_view(request):
    """Customer registration page with email support."""
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif not password or len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Log the user in
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Account created! Please complete your profile to continue.')
                return redirect('profile_onboarding')
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    # Always show Google OAuth (even if credentials not configured, button will show)
    try:
        import social_django
        context = {
            'SOCIAL_AUTH_ENABLED': True,  # Always True if social_django is installed
            **cart_context,  # Add cart info to context
        }
    except ImportError:
        context = {
            'SOCIAL_AUTH_ENABLED': False,
            **cart_context,  # Add cart info to context
        }
    return render(request, 'storefront/register.html', context)

@login_required
def profile_onboarding(request):
    """Collect required customer profile fields after registration."""
    # If customer already exists, redirect to homepage
    if Customer.objects.filter(email=request.user.email).exists():
        return redirect('homepage')
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Create required customer record
            Customer.objects.create(
                user=request.user,
                email=request.user.email,
                name=(f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username),
                age=data['age'],
                gender=data['gender'],
                employment_status=data['employment_status'],
                occupation=data['occupation'],
                education=data['education'],
                household_size=data['household_size'],
                has_children=data['has_children'],
                monthly_income_sgd=data['monthly_income_sgd'],
                preferred_category=data['preferred_category'],
            )
            messages.success(request, 'Profile completed successfully!')
            return redirect('homepage')
        else:
            messages.error(request, 'Please fix the errors below and submit again.')
    else:
        form = CustomerProfileForm()
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/profile_onboarding.html', context)

def logout_view(request):
    """Logout view."""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')

# --- Newsletter Subscription ---

@require_POST
def subscribe_newsletter(request):
    """Subscribe to newsletter via AJAX."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if email:
            subscription, created = NewsletterSubscription.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            
            if created:
                return JsonResponse({
                    'success': True,
                    'message': 'Successfully subscribed to newsletter!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Email already subscribed'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please provide a valid email'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error subscribing to newsletter'
        })