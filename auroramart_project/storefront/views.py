from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from adminpanel.models import Product, Customer
from .models import Cart, CartItem, Wishlist, WishlistItem, ProductReview, Category, SubCategory, Banner, NewsletterSubscription

# --- Utility Functions ---

def get_or_create_cart(request):
    """Get or create a cart for the current user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

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
    
    context = {
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'banners': banners,
        'categories': categories,
    }
    return render(request, 'storefront/homepage.html', context)

def product_list(request, category_slug=None, subcategory_slug=None):
    """Product listing page with filtering and search."""
    products = Product.objects.filter(stock__gt=0)
    
    # Filter by category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category.name)
        
        # Filter by subcategory
        if subcategory_slug:
            subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
            products = products.filter(subcategory=subcategory.name)
    else:
        category = None
        subcategory = None
    
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
    
    # Get categories for sidebar
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': page_obj,
        'category': category,
        'subcategory': subcategory,
        'categories': categories,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page."""
    product = get_object_or_404(Product, id=product_id)
    
    # Get reviews
    reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        stock__gt=0
    ).exclude(id=product.id)[:4]
    
    # Get frequently bought together (simple implementation)
    frequently_bought = Product.objects.filter(
        category=product.category,
        stock__gt=0
    ).exclude(id=product.id)[:5]
    
    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related_products': related_products,
        'frequently_bought': frequently_bought,
    }
    return render(request, 'storefront/product_detail.html', context)

def shopping_cart(request):
    """Shopping cart page."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
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
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'storefront/wishlist.html', context)

# --- AJAX Views for Cart Operations ---

@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price)
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
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price),
            'item_total': float(cart_item.total_price)
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
    """Add product to wishlist via AJAX."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request)
        
        if wishlist:
            wishlist_item, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product
            )
            
            if created:
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} added to wishlist'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Item already in wishlist'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to use wishlist'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding item to wishlist'
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
    """Customer login page."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('homepage')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'storefront/login.html')

def register_view(request):
    """Customer registration page."""
    if request.method == 'POST':
        # Simple registration - you can enhance this
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('homepage')
    
    return render(request, 'storefront/register.html')

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