from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
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
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
import json

from adminpanel.models import Product, Customer, Order, OrderItem
from .models import Cart, CartItem, Wishlist, WishlistItem, ProductReview, Category, SubCategory, Banner, NewsletterSubscription, SavedAddress, SavedPaymentMethod, DeliveryServiceReview, ReturnRequest, ReturnRequestItem
from .recommendations import get_recommendations, get_category_recommendations
from .forms import CustomerProfileForm, CheckoutForm, AddressForm, PaymentMethodForm, UserProfileForm, ReturnRequestForm, ReturnItemForm, ReturnRequestSubmissionForm
from .cart_helpers import get_or_create_cart, add_product_to_cart, update_cart_item_quantity
from .business_logic import (
    add_to_cart_logic, update_cart_quantity_logic, remove_from_cart_logic,
    toggle_wishlist_logic, remove_from_wishlist_logic,
    mark_review_helpful_logic, mark_review_not_helpful_logic, report_review_logic,
    subscribe_newsletter_logic
)

# --- OAuth Redirect Handler ---

def oauth_redirect_handler(request):
    """Handle OAuth redirects and check if user needs profile onboarding."""
    # Check if user is authenticated (OAuth should have logged them in)
    if request.user.is_authenticated:
        # Check if customer profile is incomplete
        try:
            customer = Customer.objects.get(user=request.user)
            if not customer.age or not customer.gender or not customer.employment_status:
                # Redirect to homepage with modal parameter
                return redirect(f"{reverse('homepage')}?show_onboarding=true")
        except Customer.DoesNotExist:
            # No customer profile exists, redirect to homepage with modal
            return redirect(f"{reverse('homepage')}?show_onboarding=true")
    
    # Profile is complete or user not authenticated, redirect to homepage
    return redirect('homepage')

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
    featured_products = Product.objects.filter(quantity_on_hand__gt=0, is_active=True).order_by('-rating')[:8]
    best_sellers = Product.objects.filter(quantity_on_hand__gt=0, is_active=True).order_by('-rating')[:8]
    
    # Get banners from database
    banners = Banner.objects.filter(is_active=True).order_by('display_order')
    
    # Load all banner images from static/images/Banner folder
    import os
    from django.conf import settings
    
    class StaticBanner:
        def __init__(self, image_path, title=None):
            self.title = title or "Welcome to AuroraMart"
            self.subtitle = "Discover amazing products at great prices"
            self.link_url = reverse('product_list')
            self.image = None
            self.image_url = image_path
    
    # Get all banner images from the Banner folder
    banner_folder = os.path.join(settings.BASE_DIR, 'storefront', 'static', 'images', 'Banner')
    static_banners = []
    
    if os.path.exists(banner_folder):
        banner_files = sorted([f for f in os.listdir(banner_folder) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])
        
        for banner_file in banner_files:
            # Create a static banner object for each image
            banner_path = f'images/Banner/{banner_file}'
            static_banner = StaticBanner(banner_path, f"Welcome to AuroraMart")
            static_banners.append(static_banner)
    
    # Combine static banners with database banners
    banners_list = static_banners + list(banners)
    banners = banners_list
    
    # Get categories for navigation
    categories = Category.objects.filter(is_active=True)
    
    # Get cart context
    cart_context = get_cart_context(request)
    cart = cart_context['cart']
    cart_product_ids = set(cart.items.values_list('product_id', flat=True))
    
    # Get wishlist product IDs
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    # Check if profile onboarding modal should be shown
    show_profile_modal = False
    profile_form = None
    if request.user.is_authenticated and request.GET.get('show_onboarding') == 'true':
        show_profile_modal = True
        profile_form = CustomerProfileForm()
    
    context = {
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'banners': banners,
        'categories': categories,
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
        'cart': cart,
        'show_profile_modal': show_profile_modal,  # For modal display
        'profile_form': profile_form,  # For modal form
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/homepage.html', context)

def product_list(request, category_slug=None, subcategory_slug=None):
    """Product listing page with filtering and search."""
    products = Product.objects.filter(quantity_on_hand__gt=0)
    
    category = None
    subcategory = None
    
    # Filter by category using database Category model
    if category_slug:
        try:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            # Filter products by category name (matching Product.category field)
            products = products.filter(category=category.name)
            
            # Filter by subcategory if provided
            if subcategory_slug:
                try:
                    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category, is_active=True)
                    # Filter products by subcategory name (matching Product.subcategory field)
                    products = products.filter(subcategory=subcategory.name)
                except SubCategory.DoesNotExist:
                    subcategory = None
        except Category.DoesNotExist:
            category = None
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(subcategory__icontains=search_query)
        )
    
    # Price Range Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            min_price = float(min_price)
            products = products.filter(price__gte=min_price)
        except ValueError:
            pass
    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Rating Filter
    filter_rating = request.GET.get('filter_rating')
    if filter_rating:
        try:
            filter_rating = int(filter_rating)
            if 1 <= filter_rating <= 5:
                # Filter products with average rating >= filter_rating
                # Since we're using the product's rating field, filter by that
                products = products.filter(rating__gte=filter_rating)
        except ValueError:
            pass
    
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
    
    # Categories are now provided by context processor (navigation_categories)
    
    # Get cart to check which products are already in cart
    cart = get_or_create_cart(request)
    cart_product_ids = set(cart.items.values_list('product_id', flat=True))
    
    # Get wishlist product IDs for logged-in users
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    # Get subcategories for the current category with product counts
    subcategories = []
    if category:
        from django.db.models import Count
        # Get subcategories from the database Category model
        db_subcategories = category.subcategories.filter(is_active=True).order_by('name')
        
        for db_subcat in db_subcategories:
            # Count products matching this subcategory name
            product_count = Product.objects.filter(
                category=category.name,
                subcategory=db_subcat.name,
                quantity_on_hand__gt=0
            ).count()
            subcategories.append({
                'name': db_subcat.name,
                'slug': db_subcat.slug,
                'count': product_count
            })
    
    # Prepare products with "Next best action" sections every 8 products
    # Group products into chunks of 8 and generate recommendations for each chunk
    products_list = list(page_obj)
    next_best_actions_dict = {}  # Dictionary mapping index to recommendations
    
    if category:
        # Process products in chunks of 8
        chunk_size = 8
        seen_product_ids = set()
        seen_product_skus = set()
        
        for i in range(0, len(products_list), chunk_size):
            chunk = products_list[i:i + chunk_size]
            
            # Track seen products
            for product in chunk:
                seen_product_ids.add(product.id)
                if product.sku:
                    seen_product_skus.add(product.sku)
            
            # Generate recommendations after each chunk (only if not the last chunk)
            if i + chunk_size < len(products_list):
                try:
                    # Get recommendations based on products in current chunk
                    chunk_skus = [p.sku for p in chunk if p.sku]
                    if chunk_skus:
                        recommendations = get_recommendations(
                            chunk_skus,
                            top_n=4  # Show 4 products in "Next best action"
                        )
                    else:
                        # Fallback: use category recommendations
                        recommendations = get_category_recommendations(
                            category.name,
                            exclude_skus=list(seen_product_skus),
                            top_n=4
                        )
                    
                    # Filter out already seen products
                    recommendations = [p for p in recommendations if p.id not in seen_product_ids]
                    
                    # If we don't have enough, fill with category products
                    if len(recommendations) < 4:
                        additional = Product.objects.filter(
                            category=category.name,
                            quantity_on_hand__gt=0
                        ).exclude(id__in=seen_product_ids).exclude(
                            id__in=[p.id for p in recommendations]
                        ).order_by('-rating')[:4 - len(recommendations)]
                        recommendations = list(recommendations) + list(additional)
                    
                    # Store recommendations at the index after this chunk
                    next_best_actions_dict[i + chunk_size] = recommendations[:4]
                    
                    # Add recommended product IDs to seen set
                    for rec_product in recommendations[:4]:
                        seen_product_ids.add(rec_product.id)
                        if rec_product.sku:
                            seen_product_skus.add(rec_product.sku)
                            
                except Exception as e:
                    # Fallback: use popular products in category
                    fallback_recs = Product.objects.filter(
                        category=category.name,
                        quantity_on_hand__gt=0
                    ).exclude(id__in=seen_product_ids).order_by('-rating')[:4]
                    
                    if fallback_recs.exists():
                        next_best_actions_dict[i + chunk_size] = list(fallback_recs)
                        for rec_product in fallback_recs:
                            seen_product_ids.add(rec_product.id)
                            if rec_product.sku:
                                seen_product_skus.add(rec_product.sku)
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'products': page_obj,
        'next_best_actions_dict': next_best_actions_dict,
        'category': category,
        'category_slug': category_slug,
        'subcategory_slug': subcategory_slug,
        'subcategory': subcategory,
        'subcategories': subcategories,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
        'cart': cart,
        'page_obj': page_obj,  # Keep for pagination
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page."""
    product = get_object_or_404(Product, id=product_id)
    
    # Get all reviews for rating distribution
    all_reviews = ProductReview.objects.filter(product=product).select_related('user').prefetch_related('images', 'helpful_votes')
    reviews_count = all_reviews.count()
    avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or float(product.rating)
    
    # Calculate star display (full stars, half stars, empty stars)
    full_stars = int(avg_rating)
    has_half_star = (avg_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)
    
    # Calculate rating distribution (1-5 stars)
    from django.db.models import Count
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = all_reviews.filter(rating=i).count()
    
    # Review sorting and filtering
    reviews = all_reviews
    sort_by = request.GET.get('sort', 'default')
    filter_rating = request.GET.get('filter_rating', None)
    
    # Filter by rating
    if filter_rating:
        try:
            filter_rating = int(filter_rating)
            if 1 <= filter_rating <= 5:
                reviews = reviews.filter(rating=filter_rating)
        except ValueError:
            pass
    
    # Annotate reviews with helpful count and not helpful count for sorting
    from django.db.models import Count, Case, When, IntegerField, Q
    reviews = reviews.annotate(
        helpful_count_annotated=Count(
            Case(
                When(helpful_votes__is_helpful=True, then=1),
                output_field=IntegerField()
            )
        ),
        not_helpful_count_annotated=Count(
            Case(
                When(helpful_votes__is_helpful=False, then=1),
                output_field=IntegerField()
            )
        )
    )
    
    # Sort reviews
    if sort_by == 'recent':
        reviews = reviews.order_by('-created_at')
    elif sort_by == 'rating_high':
        reviews = reviews.order_by('-rating', '-created_at')
    elif sort_by == 'rating_low':
        reviews = reviews.order_by('rating', '-created_at')
    elif sort_by == 'helpful':
        # Sort by helpful count descending, then push down not helpful reviews
        reviews = reviews.order_by('-helpful_count_annotated', 'not_helpful_count_annotated', '-created_at')
    else:  # default - sort by helpful count (most likes first), push down not helpful
        reviews = reviews.order_by('-helpful_count_annotated', 'not_helpful_count_annotated', '-created_at')
    
    # Get helpful votes for authenticated users
    user_helpful_review_ids = set()
    if request.user.is_authenticated:
        from storefront.models import ReviewHelpfulVote
        user_helpful_review_ids = set(
            ReviewHelpfulVote.objects.filter(
                user=request.user,
                review__product=product,
                is_helpful=True
            ).values_list('review_id', flat=True)
        )
    
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
                quantity_on_hand__gt=0
            ).exclude(id=product.id)[:5]
    except:
        frequently_bought = Product.objects.filter(
            category=product.category,
            quantity_on_hand__gt=0
        ).exclude(id=product.id)[:5]
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        quantity_on_hand__gt=0
    ).exclude(id=product.id)[:4]
    
    # Get wishlist product IDs for all products (main product + related products + frequently bought)
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            # Get wishlist IDs for all products shown on the page
            all_product_ids = [product.id]
            if related_products:
                all_product_ids.extend(list(related_products.values_list('id', flat=True)))
            if frequently_bought:
                all_product_ids.extend(list(frequently_bought.values_list('id', flat=True)))
            wishlist_product_ids = set(
                wishlist.items.filter(product_id__in=all_product_ids).values_list('product_id', flat=True)
            )
    
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
        'wishlist_product_ids': wishlist_product_ids,
        'reviews_count': reviews_count,
        'avg_rating': float(avg_rating),
        'full_stars': full_stars,
        'has_half_star': has_half_star,
        'empty_stars': empty_stars,
        'rating_distribution': rating_distribution,
        'sort_by': sort_by,
        'filter_rating': filter_rating,
        'user_helpful_review_ids': user_helpful_review_ids,
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
    
    # Get recommended products for "Complete the Set" section
    # Based on products currently in cart
    recommended_products = []
    if cart_items.exists():
        # Get SKUs of products in cart
        cart_product_skus = [item.product.sku for item in cart_items if item.product.sku]
        cart_product_ids = [item.product.id for item in cart_items]
        
        if cart_product_skus:
            try:
                from .recommendations import get_recommendations
                recommended_products = get_recommendations(cart_product_skus, top_n=4)
                # Exclude products already in cart
                recommended_products = [p for p in recommended_products if p.id not in cart_product_ids]
            except:
                pass
        
        # If we don't have enough recommendations, fill with products from same categories
        if len(recommended_products) < 4:
            from adminpanel.models import Product
            categories = set([item.product.category for item in cart_items if item.product.category])
            if categories:
                additional = Product.objects.filter(
                    category__in=categories,
                    quantity_on_hand__gt=0
                ).exclude(id__in=cart_product_ids).exclude(
                    id__in=[p.id for p in recommended_products]
                ).order_by('-rating')[:4 - len(recommended_products)]
                recommended_products = list(recommended_products) + list(additional)
        
        # If still not enough, get any popular products
        if len(recommended_products) < 4:
            from adminpanel.models import Product
            additional = Product.objects.filter(
                quantity_on_hand__gt=0
            ).exclude(id__in=cart_product_ids).exclude(
                id__in=[p.id for p in recommended_products]
            ).order_by('-rating')[:4 - len(recommended_products)]
            recommended_products = list(recommended_products) + list(additional)
    else:
        # If cart is empty, show popular products
        from adminpanel.models import Product
        recommended_products = Product.objects.filter(quantity_on_hand__gt=0).order_by('-rating')[:4]
    
    # Limit to 4 products for the cart page
    recommended_products = recommended_products[:4]
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    # Get wishlist product IDs for authenticated users
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    # Get cart product IDs
    cart_product_ids = set([item.product.id for item in cart_items])
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'recommended_products': recommended_products,
        'wishlist_product_ids': wishlist_product_ids,
        'cart_product_ids': cart_product_ids,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/shopping_cart.html', context)

@login_required
def checkout(request):
    """Checkout page and order processing."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Check if cart is empty
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty. Add some items before checkout.')
        return redirect('shopping_cart')
    
    # Get customer profile - redirect to onboarding if not complete
    # But only if show_onboarding parameter is not already present (to avoid redirect loop)
    if request.GET.get('show_onboarding') != 'true':
        try:
            customer = Customer.objects.get(user=request.user)
            # Check if profile is properly filled
            if not customer.age or not customer.gender or not customer.employment_status:
                # Only show message once per checkout attempt (use session flag)
                if not request.session.get('checkout_profile_message_shown', False):
                    messages.info(request, 'Please complete your profile before checkout.')
                    request.session['checkout_profile_message_shown'] = True
                # Include next parameter to redirect back to checkout after profile completion
                return redirect(f"{reverse('checkout')}?show_onboarding=true&next={reverse('checkout')}")
        except Customer.DoesNotExist:
            # Redirect to show profile onboarding modal
            # Only show message once per checkout attempt (use session flag)
            if not request.session.get('checkout_profile_message_shown', False):
                messages.info(request, 'Please complete your profile before checkout.')
                request.session['checkout_profile_message_shown'] = True
            # Include next parameter to redirect back to checkout after profile completion
            return redirect(f"{reverse('checkout')}?show_onboarding=true&next={reverse('checkout')}")
    else:
        # If show_onboarding is true, clear the session flag so message can be shown again if needed
        # (This allows the message to be shown again if user comes back to checkout later)
        if request.session.get('checkout_profile_message_shown', False):
            # Keep the flag if profile is still incomplete, clear it if profile is complete
            try:
                customer = Customer.objects.get(user=request.user)
                if customer.age and customer.gender and customer.employment_status:
                    # Profile is now complete, clear the flag
                    request.session.pop('checkout_profile_message_shown', None)
            except Customer.DoesNotExist:
                pass
    
    # Get saved addresses and payment methods
    saved_addresses = SavedAddress.objects.filter(user=request.user)
    saved_payment_methods = SavedPaymentMethod.objects.filter(user=request.user)
    
    # Calculate totals (will be updated based on delivery time)
    from decimal import Decimal
    subtotal = cart.total_price
    
    if request.method == 'POST':
        # Check if this is just saving an address
        if request.POST.get('save_address_only'):
            from django.http import JsonResponse
            try:
                full_name = request.POST.get('full_name')
                phone_number = request.POST.get('phone_number')
                address = request.POST.get('address')
                city = request.POST.get('city')
                postal_code = request.POST.get('postal_code')
                country = request.POST.get('country')
                floor_unit_number = request.POST.get('floor_unit_number', '')
                
                if not all([full_name, phone_number, address, city, postal_code, country]):
                    return JsonResponse({'success': False, 'error': 'Please fill in all required fields'})
                
                SavedAddress.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone_number=phone_number,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    floor_unit_number=floor_unit_number,
                    is_default=not saved_addresses.exists()
                )
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address_data = form.cleaned_data
            
            # Get shipping address - check raw POST data first
            saved_address_id = request.POST.get('saved_address_id')
            if saved_address_id and saved_address_id != '':
                # Use saved address
                saved_address = get_object_or_404(SavedAddress, id=saved_address_id, user=request.user)
                shipping_address = saved_address.get_formatted_address()
            else:
                # Use new address
                floor_unit = f", {address_data['floor_unit_number']}" if address_data.get('floor_unit_number') else ""
                shipping_address = (
                    f"{address_data['full_name']}\n"
                    f"{address_data['phone_number']}\n"
                    f"{address_data['address']}{floor_unit}\n"
                    f"{address_data['city']}, {address_data['postal_code']}\n"
                    f"{address_data['country']}"
                )
                
                # Save address if requested
                if address_data.get('save_address'):
                    SavedAddress.objects.create(
                        user=request.user,
                        full_name=address_data['full_name'],
                        phone_number=address_data['phone_number'],
                        address=address_data['address'],
                        city=address_data['city'],
                        postal_code=address_data['postal_code'],
                        country=address_data['country'],
                        floor_unit_number=address_data.get('floor_unit_number', ''),
                        is_default=not saved_addresses.exists()  # First address is default
                    )
            
            # Get payment method - check raw POST data first
            saved_payment_id = request.POST.get('saved_payment_id')
            if saved_payment_id and saved_payment_id != '':
                # Use saved payment method
                saved_payment = get_object_or_404(SavedPaymentMethod, id=saved_payment_id, user=request.user)
                payment_method = saved_payment.payment_type
            else:
                # Use new payment method
                payment_method = address_data['payment_method']
                
                # Save payment method if it's a card
                if payment_method == 'card' and address_data.get('card_number'):
                    card_number = address_data['card_number'].replace(' ', '')
                    card_last_four = card_number[-4:] if len(card_number) >= 4 else ''
                    SavedPaymentMethod.objects.create(
                        user=request.user,
                        payment_type='card',
                        cardholder_name=address_data['cardholder_name'],
                        card_last_four=card_last_four,
                        card_expiry=address_data['card_expiry'],
                        is_default=not saved_payment_methods.exists()
                    )
            
            # Get delivery time and calculate shipping fee
            delivery_time = request.POST.get('delivery_time') or address_data.get('delivery_time', 'standard')
            if delivery_time == 'standard':
                shipping_fee = Decimal('0.00')
            elif delivery_time == 'express':
                shipping_fee = Decimal('4.99')
            elif delivery_time == 'overnight':
                shipping_fee = Decimal('12.99')
            else:
                shipping_fee = Decimal('0.00')
            
            total = subtotal + shipping_fee
            
            # Validate stock availability before creating order
            out_of_stock_items = []
            for cart_item in cart_items:
                if cart_item.product.quantity_on_hand < cart_item.quantity:
                    out_of_stock_items.append(cart_item.product.name)
            
            if out_of_stock_items:
                messages.error(request, f'Some items are out of stock: {", ".join(out_of_stock_items)}')
                return redirect('shopping_cart')
            
            # Create order
            try:
                order = Order.objects.create(
                    customer=customer,
                    total_amount=total,
                    shipping_address=shipping_address,
                    fulfillment_status='PENDING',
                    payment_method=payment_method,  # Save payment method
                    delivery_time=delivery_time      # Save delivery time
                )
                
                # Create order items and update product stock
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.product.price
                    )
                    
                    # Update product stock (quantity_on_hand)
                    cart_item.product.quantity_on_hand -= cart_item.quantity
                    cart_item.product.save()
                
                # Clear the cart
                cart_items.delete()
                
                messages.success(request, f'Order placed successfully! Order ID: {order.oID}')
                return redirect('my_orders')
                
            except Exception as e:
                messages.error(request, f'Error creating order: {str(e)}')
                return redirect('shopping_cart')
        else:
            # Form is invalid - preserve POST data so user doesn't lose their selections
            # Show specific form errors for debugging
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        error_messages.append(f"{field}: {error}")
            if error_messages:
                messages.error(request, f'Please fix the errors: {"; ".join(error_messages)}')
            else:
                messages.error(request, 'Please fix the errors below and try again.')
    else:
        form = CheckoutForm()
        # Set initial delivery time
        form.fields['delivery_time'].initial = 'standard'
    
    # Calculate initial shipping fee (standard delivery)
    shipping_fee = Decimal('0.00')
    total = subtotal + shipping_fee
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'saved_addresses': saved_addresses,
        'saved_payment_methods': saved_payment_methods,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/checkout.html', context)

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

def complete_the_set(request):
    """Complete the Set page showing all recommended products."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Get all recommended products for "Complete the Set" section
    recommended_products = []
    if cart_items.exists():
        # Get SKUs of products in cart
        cart_product_skus = [item.product.sku for item in cart_items if item.product.sku]
        cart_product_ids = [item.product.id for item in cart_items]
        
        if cart_product_skus:
            try:
                from .recommendations import get_recommendations
                recommended_products = get_recommendations(cart_product_skus, top_n=20)
                # Exclude products already in cart
                recommended_products = [p for p in recommended_products if p.id not in cart_product_ids]
            except:
                pass
        
        # If we don't have enough recommendations, fill with products from same categories
        if len(recommended_products) < 20:
            from adminpanel.models import Product
            categories = set([item.product.category for item in cart_items if item.product.category])
            if categories:
                additional = Product.objects.filter(
                    category__in=categories,
                    quantity_on_hand__gt=0
                ).exclude(id__in=cart_product_ids).exclude(
                    id__in=[p.id for p in recommended_products]
                ).order_by('-rating')[:20 - len(recommended_products)]
                recommended_products = list(recommended_products) + list(additional)
        
        # If still not enough, get any popular products
        if len(recommended_products) < 20:
            from adminpanel.models import Product
            additional = Product.objects.filter(
                quantity_on_hand__gt=0
            ).exclude(id__in=cart_product_ids).exclude(
                id__in=[p.id for p in recommended_products]
            ).order_by('-rating')[:20 - len(recommended_products)]
            recommended_products = list(recommended_products) + list(additional)
    else:
        # If cart is empty, show popular products
        from adminpanel.models import Product
        recommended_products = Product.objects.filter(quantity_on_hand__gt=0).order_by('-rating')[:20]
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    # Get wishlist product IDs for authenticated users
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist = get_or_create_wishlist(request)
        if wishlist:
            wishlist_product_ids = set(wishlist.items.values_list('product_id', flat=True))
    
    # Get cart product IDs
    cart_product_ids = set([item.product.id for item in cart_items])
    
    context = {
        'recommended_products': recommended_products,
        'wishlist_product_ids': wishlist_product_ids,
        'cart_product_ids': cart_product_ids,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/complete_the_set.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail page showing order items with review buttons."""
    from adminpanel.models import Order, OrderItem
    from storefront.models import ProductReview
    from datetime import timedelta
    
    # Get order and verify it belongs to the user
    try:
        customer = Customer.objects.get(user=request.user)
        order = get_object_or_404(Order, id=order_id, customer=customer)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('my_orders')
    
    # Get order items with calculated totals
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    order_items_with_totals = []
    for item in order_items:
        item.total_price = item.unit_price * item.quantity
        order_items_with_totals.append(item)
    
    # Calculate delivery time (add 1 day to placed_at, set to 5pm)
    delivery_datetime = order.placed_at + timedelta(days=1)
    delivery_datetime = delivery_datetime.replace(hour=17, minute=0, second=0, microsecond=0)
    # Format delivery time as "Mon 10 Nov, 5pm" (capitalize first letter of day and month)
    delivery_time_formatted = delivery_datetime.strftime("%a %d %b, %I%p").lower()
    # Capitalize first letter of day and month
    parts = delivery_time_formatted.split()
    if len(parts) >= 3:
        parts[0] = parts[0].capitalize()  # Day
        parts[2] = parts[2].capitalize()  # Month
        delivery_time_formatted = ' '.join(parts)
    
    # Check which products have been reviewed
    reviewed_product_ids = set(
        ProductReview.objects.filter(
            user=request.user,
            product__in=[item.product for item in order_items]
        ).values_list('product_id', flat=True)
    )
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'order': order,
        'order_items': order_items_with_totals,
        'delivery_time_formatted': delivery_time_formatted,
        'reviewed_product_ids': reviewed_product_ids,
        **cart_context,
    }
    return render(request, 'storefront/order_detail.html', context)

@login_required
def submit_review(request, order_id, product_id):
    """Submit a review for a product from an order."""
    from adminpanel.models import Order, OrderItem, Product
    from storefront.models import ProductReview, ReviewImage, DeliveryServiceReview
    from .forms import ProductReviewForm, DeliveryServiceReviewForm
    
    # Verify order belongs to user
    try:
        customer = Customer.objects.get(user=request.user)
        order = get_object_or_404(Order, id=order_id, customer=customer)
        product = get_object_or_404(Product, id=product_id)
        
        # Verify product is in the order
        order_item = OrderItem.objects.filter(order=order, product=product).first()
        if not order_item:
            messages.error(request, 'This product is not in your order.')
            return redirect('order_detail', order_id=order_id)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('my_orders')
    
    # Check if reviews already exist
    existing_review = ProductReview.objects.filter(user=request.user, product=product).first()
    existing_delivery_review = DeliveryServiceReview.objects.filter(user=request.user, order=order).first()
    
    if request.method == 'POST':
        # Handle product review submission
        if 'submit_product_review' in request.POST:
            # Get rating from POST data (from hidden input)
            post_data = request.POST.copy()
            if 'rating' in post_data:
                rating_value = post_data.get('rating')
                if rating_value:
                    post_data['rating'] = rating_value
            
            # Get anonymous status from checkbox
            post_data['is_anonymous'] = 'is_anonymous' in request.POST
            
            form = ProductReviewForm(post_data, request.FILES)
            if form.is_valid():
                # Create or update review
                if existing_review:
                    existing_review.rating = int(form.cleaned_data.get('rating', existing_review.rating))
                    existing_review.title = form.cleaned_data['title']
                    existing_review.comment = form.cleaned_data['comment']
                    existing_review.is_verified_purchase = True
                    existing_review.is_anonymous = form.cleaned_data.get('is_anonymous', False)
                    existing_review.save()
                    review = existing_review
                else:
                    review = ProductReview.objects.create(
                        user=request.user,
                        product=product,
                        rating=int(form.cleaned_data.get('rating', 5)),
                        title=form.cleaned_data['title'],
                        comment=form.cleaned_data['comment'],
                        is_verified_purchase=True,
                        is_anonymous=form.cleaned_data.get('is_anonymous', False)
                    )
                
                # Handle image upload
                if 'image' in request.FILES and request.FILES['image']:
                    ReviewImage.objects.filter(review=review).delete()
                    ReviewImage.objects.create(
                        review=review,
                        image=request.FILES['image']
                    )
                
                messages.success(request, 'Thank you for your product review!')
        
        # Handle delivery service review submission
        if 'submit_delivery_review' in request.POST:
            delivery_post_data = request.POST.copy()
            if 'delivery_rating' in delivery_post_data:
                delivery_rating_value = delivery_post_data.get('delivery_rating')
                if delivery_rating_value:
                    delivery_post_data['rating'] = delivery_rating_value
            
            delivery_form = DeliveryServiceReviewForm(delivery_post_data)
            
            if delivery_form.is_valid():
                if existing_delivery_review:
                    existing_delivery_review.rating = int(delivery_form.cleaned_data.get('rating', existing_delivery_review.rating))
                    existing_delivery_review.comment = delivery_form.cleaned_data.get('comment', '')
                    existing_delivery_review.is_anonymous = False  # Delivery reviews are never anonymous
                    existing_delivery_review.save()
                else:
                    DeliveryServiceReview.objects.create(
                        user=request.user,
                        order=order,
                        rating=int(delivery_form.cleaned_data.get('rating', 5)),
                        comment=delivery_form.cleaned_data.get('comment', ''),
                        is_anonymous=False  # Delivery reviews are never anonymous
                    )
                
                messages.success(request, 'Thank you for your delivery service review!')
        
        return redirect('order_detail', order_id=order_id)
    else:
        # Pre-fill forms if reviews exist
        if existing_review:
            form = ProductReviewForm(initial={
                'rating': existing_review.rating,
                'title': existing_review.title,
                'comment': existing_review.comment,
                'is_anonymous': existing_review.is_anonymous,
            })
        else:
            form = ProductReviewForm()
        
        if existing_delivery_review:
            delivery_form = DeliveryServiceReviewForm(initial={
                'rating': existing_delivery_review.rating,
                'comment': existing_delivery_review.comment,
            })
        else:
            delivery_form = DeliveryServiceReviewForm()
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'delivery_form': delivery_form,
        'order': order,
        'product': product,
        'order_item': order_item,
        'existing_review': existing_review,
        'existing_delivery_review': existing_delivery_review,
        **cart_context,
    }
    return render(request, 'storefront/submit_review.html', context)

@login_required
def my_orders(request):
    """User's orders page showing past orders."""
    from adminpanel.models import Order, OrderItem
    from datetime import timedelta
    
    # Get customer associated with the user
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        # If customer doesn't exist, show empty orders
        customer = None
    
    # Get all orders for this customer, ordered by most recent first
    if customer:
        orders = Order.objects.filter(customer=customer).order_by('-placed_at')
        
        # Prepare order data with delivery time and item counts
        orders_data = []
        for order in orders:
            # Calculate delivery time (add 1 day to placed_at, set to 5pm)
            delivery_datetime = order.placed_at + timedelta(days=1)
            delivery_datetime = delivery_datetime.replace(hour=17, minute=0, second=0, microsecond=0)
            # Format delivery time as "Mon 10 Nov, 5pm" (capitalize first letter of day and month)
            delivery_time_formatted = delivery_datetime.strftime("%a %d %b, %I%p").lower()
            # Capitalize first letter of day and month
            parts = delivery_time_formatted.split()
            if len(parts) >= 3:
                parts[0] = parts[0].capitalize()  # Day
                parts[2] = parts[2].capitalize()  # Month
                delivery_time_formatted = ' '.join(parts)
            
            # Get order items with products
            order_items = OrderItem.objects.filter(order=order).select_related('product')
            total_items = sum(item.quantity for item in order_items)
            
            # Get product images (first 6 items)
            product_images = []
            for item in order_items[:6]:
                if item.product and item.product.image:
                    product_images.append(item.product.image.url)
                else:
                    product_images.append(None)  # Placeholder for missing image
            
            # Check if there are more items
            has_more_items = len(order_items) > 6
            
            orders_data.append({
                'order': order,
                'delivery_datetime': delivery_datetime,
                'delivery_time_formatted': delivery_time_formatted,
                'order_items': order_items,
                'total_items': total_items,
                'product_images': product_images,
                'has_more_items': has_more_items,
                'remaining_items_count': len(order_items) - 6 if has_more_items else 0,
            })
    else:
        orders_data = []
    
    # Get cart context
    cart_context = get_cart_context(request)
    
    context = {
        'orders_data': orders_data,
        **cart_context,  # Add cart info to context
    }
    return render(request, 'storefront/my_orders.html', context)

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
    """Add product to cart via form submission or AJAX."""
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        if not product_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)
            messages.error(request, 'Product ID is required')
            return redirect(redirect_url)
        
        success, message = add_to_cart_logic(request, product_id, quantity)
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = get_or_create_cart(request)
            cart_total_items = cart.total_items if cart else 0
            return JsonResponse({
                'success': success,
                'message': message,
                'cart_count': cart_total_items
            })
        
        # Otherwise, redirect as before
        return redirect(redirect_url)
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error adding item to cart'}, status=500)
        messages.error(request, 'Error adding item to cart')
        return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def update_cart_item(request):
    """Update cart item quantity via form submission or AJAX."""
    try:
        item_id = request.POST.get('item_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/cart/'))
        
        if not item_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Item ID is required'}, status=400)
            messages.error(request, 'Item ID is required')
            return redirect(redirect_url)
        
        # Support both absolute quantity and action-based updates
        if 'quantity' in request.POST:
            quantity = int(request.POST.get('quantity', 1))
        elif 'action' in request.POST:
            # Handle increment/decrement actions
            cart_item = get_object_or_404(CartItem, id=item_id)
            action = request.POST.get('action')
            if action == 'increase':
                quantity = cart_item.quantity + 1
            elif action == 'decrease':
                quantity = max(0, cart_item.quantity - 1)
            else:
                quantity = cart_item.quantity
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Quantity or action is required'}, status=400)
            messages.error(request, 'Quantity or action is required')
            return redirect(redirect_url)
        
        success, message, removed = update_cart_quantity_logic(request, item_id, quantity)
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = get_or_create_cart(request)
            cart_total_items = cart.total_items if cart else 0
            # Get updated quantity if item still exists
            updated_quantity = 0
            if not removed:
                try:
                    updated_cart_item = CartItem.objects.get(id=item_id)
                    updated_quantity = updated_cart_item.quantity
                except CartItem.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': success,
                'message': message,
                'removed': removed,
                'quantity': updated_quantity,
                'cart_count': cart_total_items
            })
        
        # Otherwise, redirect as before
        return redirect(redirect_url)
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error updating cart item'}, status=500)
        messages.error(request, 'Error updating cart item')
        return redirect(request.META.get('HTTP_REFERER', '/cart/'))

@require_POST
def remove_from_cart(request):
    """Remove item from cart via form submission."""
    try:
        item_id = request.POST.get('item_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/cart/'))
        
        if not item_id:
            messages.error(request, 'Item ID is required')
            return redirect(redirect_url)
        
        success, message = remove_from_cart_logic(request, item_id)
        return redirect(redirect_url)
    
    except Exception as e:
        messages.error(request, 'Error removing item from cart')
        return redirect(request.META.get('HTTP_REFERER', '/cart/'))

# --- Wishlist AJAX Views ---

@require_POST
def add_to_wishlist(request):
    """Toggle product in wishlist via form submission (add if not present, remove if present)."""
    try:
        product_id = request.POST.get('product_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        if not product_id:
            messages.error(request, 'Product ID is required')
            return redirect(redirect_url)
        
        success, message, in_wishlist = toggle_wishlist_logic(request, product_id)
        return redirect(redirect_url)
    
    except Exception as e:
        messages.error(request, 'Error updating wishlist')
        return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
@login_required
def remove_from_wishlist(request):
    """Remove item from wishlist via form submission."""
    try:
        item_id = request.POST.get('item_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/wishlist/'))
        
        if not item_id:
            messages.error(request, 'Item ID is required')
            return redirect(redirect_url)
        
        success, message = remove_from_wishlist_logic(request, item_id)
        return redirect(redirect_url)
    
    except Exception as e:
        messages.error(request, 'Error removing item from wishlist')
        return redirect(request.META.get('HTTP_REFERER', '/wishlist/'))

# --- Authentication Views ---

class CustomPasswordResetView(BasePasswordResetView):
    """Custom password reset view that blocks Google OAuth users."""
    template_name = 'storefront/password_reset.html'
    email_template_name = 'storefront/password_reset_email.html'
    subject_template_name = 'storefront/password_reset_subject.txt'
    success_url = '/password-reset/done/'
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        
        if email:
            # Check if any users with this email exist
            users_with_email = User.objects.filter(email=email)
            
            if users_with_email.exists():
                # Check if any of these users signed up with Google OAuth
                try:
                    import social_django
                    from social_django.models import UserSocialAuth
                    
                    # Check if any user with this email has Google OAuth
                    user_ids = users_with_email.values_list('id', flat=True)
                    has_google_auth = UserSocialAuth.objects.filter(
                        user_id__in=user_ids,
                        provider='google-oauth2'
                    ).exists()
                    
                    if has_google_auth:
                        messages.error(
                            request,
                            'Password reset is not available for accounts signed up with Google. '
                            'Please sign in using your Google account.'
                        )
                        # Return form with error message
                        from django.contrib.auth.forms import PasswordResetForm
                        form = PasswordResetForm()
                        return render(request, self.template_name, {'form': form})
                except ImportError:
                    # social_django not installed, proceed normally
                    pass
                except Exception:
                    # If there's any error checking, proceed normally
                    pass
                    
            # If no users exist, Django's default behavior is to still show success
            # to prevent email enumeration, so we'll keep that behavior
            # (users_with_email.exists() will be False, but we proceed anyway)
        
        # Proceed with normal password reset for email/password users
        return super().post(request, *args, **kwargs)

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
                # Handle case where multiple users might have the same email
                user_objs = User.objects.filter(email=email_or_username)
                # Try to authenticate with each user until one succeeds
                for user_obj in user_objs:
                    authenticated_user = authenticate(request, username=user_obj.username, password=password)
                    if authenticated_user:
                        user = authenticated_user
                        break
            except Exception:
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
                            if user_item.quantity > user_item.product.quantity_on_hand:
                                user_item.quantity = user_item.product.quantity_on_hand
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
                return redirect(f"{reverse('homepage')}?show_onboarding=true")
    
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
    """Collect required customer profile fields after registration - supports both page and modal."""
    # If this is accessed directly (not via modal), redirect to homepage with modal parameter
    # This ensures users always see the modal, not the standalone page
    if not request.GET.get('modal') == 'true' and not request.POST.get('modal') == 'true':
        # Check if customer profile is incomplete
        try:
            customer = Customer.objects.get(user=request.user)
            if not customer.age or not customer.gender or not customer.employment_status:
                # Redirect to homepage with modal
                next_url = request.GET.get('next') or request.META.get('HTTP_REFERER', '/')
                if '?' in next_url:
                    base_url = next_url.split('?')[0]
                else:
                    base_url = next_url
                return redirect(f"{base_url}?show_onboarding=true")
        except Customer.DoesNotExist:
            # No customer profile, redirect to homepage with modal
            next_url = request.GET.get('next') or request.META.get('HTTP_REFERER', '/')
            if '?' in next_url:
                base_url = next_url.split('?')[0]
            else:
                base_url = next_url
            return redirect(f"{base_url}?show_onboarding=true")
    
    # Check if customer already exists (by user or email)
    customer = None
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        try:
            # Check by email in case customer exists but user is not linked
            customer = Customer.objects.get(email=request.user.email)
            # Link the user to the existing customer
            customer.user = request.user
            customer.save()
        except Customer.DoesNotExist:
            customer = None
    
    # If customer exists and has been properly filled, check if they came from checkout
    # (This handles cases where user might refresh or navigate back)
    if customer and customer.age and customer.gender and customer.employment_status:
        next_url = request.GET.get('next')
        if next_url and 'checkout' in next_url:
            return redirect('checkout')
        return redirect('homepage')
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Calculate age from date of birth
            from datetime import date
            date_of_birth = data['date_of_birth']
            today = date.today()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            # Additional age validation (double-check)
            if age < 14:
                messages.error(request, 'You must be at least 14 years old to register for an account.')
                form = CustomerProfileForm(request.POST)
                # Check if this should be shown as modal
                show_modal = request.GET.get('modal') == 'true' or request.POST.get('modal') == 'true'
                if show_modal:
                    # Redirect to current page with modal parameter to show errors
                    next_url = request.GET.get('next') or request.POST.get('next') or '/'
                    return redirect(f"{next_url}?show_onboarding=true")
                cart_context = get_cart_context(request)
                context = {
                    'form': form,
                    **cart_context,
                }
                return render(request, 'storefront/profile_onboarding.html', context)
            
            # Create or update customer record
            if customer:
                # Update existing customer
                customer.user = request.user  # Ensure user is linked
                customer.email = request.user.email  # Ensure email matches
                customer.name = (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username)
                customer.age = age
                customer.gender = data['gender']
                customer.employment_status = data['employment_status']
                customer.occupation = data['occupation']
                customer.education = data['education']
                customer.household_size = data['household_size']
                customer.has_children = data['has_children']
                customer.monthly_income_sgd = data['monthly_income_sgd']
                # NOTE: preferred_category is auto-predicted by ML model in admin panel
                customer.save()
            else:
                # Create new customer record using get_or_create to avoid duplicate email errors
                customer, created = Customer.objects.get_or_create(
                    email=request.user.email,
                    defaults={
                        'user': request.user,
                        'name': (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username),
                        'age': age,
                        'gender': data['gender'],
                        'employment_status': data['employment_status'],
                        'occupation': data['occupation'],
                        'education': data['education'],
                        'household_size': data['household_size'],
                        'has_children': data['has_children'],
                        'monthly_income_sgd': data['monthly_income_sgd'],
                        'preferred_category': 'Electronics',  # Default placeholder, will be ML-predicted by admin
                    }
                )
                # If customer already existed, update it
                if not created:
                    customer.user = request.user
                    customer.name = (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username)
                    customer.age = age
                    customer.gender = data['gender']
                    customer.employment_status = data['employment_status']
                    customer.occupation = data['occupation']
                    customer.education = data['education']
                    customer.household_size = data['household_size']
                    customer.has_children = data['has_children']
                    customer.monthly_income_sgd = data['monthly_income_sgd']
                    # NOTE: preferred_category is NOT updated here - it's ML-predicted in admin panel
                    customer.save()
            
            messages.success(request, 'Profile completed successfully!')
            # Clear the checkout profile message flag since profile is now complete
            request.session.pop('checkout_profile_message_shown', None)
            # Redirect back to checkout if they came from checkout, otherwise go to homepage
            # Remove show_onboarding parameter if present
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and 'checkout' in next_url:
                return redirect('checkout')
            return redirect('homepage')
        else:
            messages.error(request, 'Please fix the errors below and submit again.')
            # If modal was used, store form data in session and redirect back
            if request.POST.get('modal') == 'true':
                # Store form data in session to repopulate form
                request.session['profile_form_data'] = request.POST.dict()
                request.session['profile_form_errors'] = True
                next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '/')
                # Remove any existing show_onboarding parameter
                if '?' in next_url:
                    base_url = next_url.split('?')[0]
                else:
                    base_url = next_url
                return redirect(f"{base_url}?show_onboarding=true")
    else:
        form = CustomerProfileForm()
        # Pre-fill form if customer exists (for updates)
        if customer:
            # Calculate approximate date of birth from age (use Jan 1st of the year)
            from datetime import date
            today = date.today()
            # Approximate DOB: assume birthday is Jan 1st of the year they were born
            approximate_dob = date(today.year - customer.age, 1, 1)
            
            form = CustomerProfileForm(initial={
                'birth_month': str(approximate_dob.month),
                'birth_day': approximate_dob.day,
                'birth_year': approximate_dob.year,
                'date_of_birth': approximate_dob,
                'gender': customer.gender,
                'employment_status': customer.employment_status,
                'occupation': customer.occupation,
                'education': customer.education,
                'household_size': customer.household_size,
                'has_children': customer.has_children,
                'monthly_income_sgd': customer.monthly_income_sgd,
            })
    
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

# --- Review API Endpoints ---

@require_POST
@login_required
def review_helpful(request):
    """Mark a review as helpful or remove helpful vote via form submission."""
    try:
        review_id = request.POST.get('review_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        if not review_id:
            messages.error(request, 'Review ID is required')
            return redirect(redirect_url)
        
        success, is_helpful, helpful_count = mark_review_helpful_logic(request, review_id)
        if success:
            messages.success(request, 'Review marked as helpful' if is_helpful else 'Helpful vote removed')
        else:
            messages.error(request, 'Error updating review helpful status')
        
        return redirect(redirect_url)
    except Exception as e:
        messages.error(request, 'Error updating review helpful status')
        return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
@login_required
def review_not_helpful(request):
    """Mark a review as not helpful via form submission."""
    try:
        review_id = request.POST.get('review_id')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        if not review_id:
            messages.error(request, 'Review ID is required')
            return redirect(redirect_url)
        
        success, is_not_helpful, helpful_count, not_helpful_count = mark_review_not_helpful_logic(request, review_id)
        if success:
            messages.success(request, 'Review marked as not helpful')
        else:
            messages.error(request, 'Error updating review status')
        
        return redirect(redirect_url)
    except Exception as e:
        messages.error(request, 'Error updating review status')
        return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
@login_required
def review_report(request):
    """Report a review for abuse via form submission."""
    try:
        review_id = request.POST.get('review_id')
        reason = request.POST.get('reason')
        additional_comments = request.POST.get('additional_comments', '')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        if not review_id or not reason:
            messages.error(request, 'Review ID and reason are required')
            return redirect(redirect_url)
        
        success, message = report_review_logic(request, review_id, reason, additional_comments)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect(redirect_url)
    except Exception as e:
        messages.error(request, 'Error submitting report')
        return redirect(request.META.get('HTTP_REFERER', '/'))

# --- Newsletter Subscription ---

@require_POST
def subscribe_newsletter(request):
    """Subscribe to newsletter via form submission."""
    try:
        email = request.POST.get('email')
        redirect_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        
        success, message = subscribe_newsletter_logic(request, email)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect(redirect_url)
    except Exception as e:
        messages.error(request, 'Error subscribing to newsletter')
        return redirect(request.META.get('HTTP_REFERER', '/'))

# --- Account Management Views ---

@login_required
def account_profile(request):
    """My Profile page - edit user and customer profile."""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please complete your profile first.')
        return redirect(f"{reverse('homepage')}?show_onboarding=true")
    
    user_form = None
    customer_form = None
    
    if request.method == 'POST':
        if 'update_user' in request.POST:
            user_form = UserProfileForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('account_profile')
        elif 'update_customer' in request.POST:
            customer_form = CustomerProfileForm(request.POST, instance=customer)
            if customer_form.is_valid():
                # Handle date of birth to age conversion
                date_of_birth = customer_form.cleaned_data.get('date_of_birth')
                if date_of_birth:
                    from datetime import date
                    today = date.today()
                    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                    
                    # Additional age validation (double-check)
                    if age < 14:
                        messages.error(request, 'You must be at least 14 years old. Your profile cannot be updated to an age below 14.')
                        user_form = UserProfileForm(instance=request.user)
                        # Recalculate date of birth from age for the form
                        from datetime import date, timedelta
                        if customer.age:
                            birth_year = date.today().year - customer.age
                            approximate_dob = date(birth_year, 1, 1)
                            customer_form = CustomerProfileForm(instance=customer, initial={
                                'birth_month': str(approximate_dob.month),
                                'birth_day': approximate_dob.day,
                                'birth_year': approximate_dob.year,
                                'date_of_birth': approximate_dob,
                            })
                        else:
                            customer_form = CustomerProfileForm(instance=customer)
                        cart_context = get_cart_context(request)
                        context = {
                            'user_form': user_form,
                            'customer_form': customer_form,
                            'customer': customer,
                            **cart_context,
                        }
                        return render(request, 'storefront/account_profile.html', context)
                    
                    customer.age = age
                
                customer_form.save()
                messages.success(request, 'Customer profile updated successfully!')
                return redirect('account_profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        # Calculate date of birth from age for the form
        from datetime import date, timedelta
        if customer.age:
            birth_year = date.today().year - customer.age
            approximate_dob = date(birth_year, 1, 1)
            customer_form = CustomerProfileForm(instance=customer, initial={
                'birth_month': str(approximate_dob.month),
                'birth_day': approximate_dob.day,
                'birth_year': approximate_dob.year,
                'date_of_birth': approximate_dob,
            })
        else:
            customer_form = CustomerProfileForm(instance=customer)
    
    cart_context = get_cart_context(request)
    
    context = {
        'user_form': user_form,
        'customer_form': customer_form,
        'customer': customer,
        **cart_context,
    }
    return render(request, 'storefront/account_profile.html', context)


@login_required
def account_addresses(request):
    """My Addresses page - list and manage saved addresses."""
    addresses = SavedAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    cart_context = get_cart_context(request)
    
    context = {
        'addresses': addresses,
        **cart_context,
    }
    return render(request, 'storefront/account_addresses.html', context)


@login_required
def account_address_add(request):
    """Add a new address."""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset other defaults
            if address.is_default:
                SavedAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('account_addresses')
    else:
        form = AddressForm()
    
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'action': 'Add',
        **cart_context,
    }
    return render(request, 'storefront/account_address_form.html', context)


@login_required
def account_address_edit(request, address_id):
    """Edit an existing address."""
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            
            # If this is set as default, unset other defaults
            if address.is_default:
                SavedAddress.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('account_addresses')
    else:
        form = AddressForm(instance=address)
    
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'address': address,
        'action': 'Edit',
        **cart_context,
    }
    return render(request, 'storefront/account_address_form.html', context)


@login_required
@require_POST
def account_address_delete(request, address_id):
    """Delete an address."""
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('account_addresses')


@login_required
def account_payment_methods(request):
    """My Payment Methods page - list and manage saved payment methods."""
    payment_methods = SavedPaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    cart_context = get_cart_context(request)
    
    context = {
        'payment_methods': payment_methods,
        **cart_context,
    }
    return render(request, 'storefront/account_payment_methods.html', context)


@login_required
def account_payment_add(request):
    """Add a new payment method."""
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.user = request.user
            
            # If this is set as default, unset other defaults
            if payment_method.is_default:
                SavedPaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            payment_method.save()
            messages.success(request, 'Payment method added successfully!')
            return redirect('account_payment_methods')
    else:
        form = PaymentMethodForm()
    
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'action': 'Add',
        **cart_context,
    }
    return render(request, 'storefront/account_payment_form.html', context)


@login_required
def account_payment_edit(request, payment_id):
    """Edit an existing payment method."""
    payment_method = get_object_or_404(SavedPaymentMethod, id=payment_id, user=request.user)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=payment_method)
        if form.is_valid():
            payment_method = form.save(commit=False)
            
            # If this is set as default, unset other defaults
            if payment_method.is_default:
                SavedPaymentMethod.objects.filter(user=request.user, is_default=True).exclude(id=payment_method.id).update(is_default=False)
            
            payment_method.save()
            messages.success(request, 'Payment method updated successfully!')
            return redirect('account_payment_methods')
    else:
        form = PaymentMethodForm(instance=payment_method)
        # Pre-fill card number with masked value for display (not editable)
        if payment_method.payment_type == 'card' and payment_method.card_last_four:
            form.fields['card_number'].initial = '**** **** **** ' + payment_method.card_last_four
    
    cart_context = get_cart_context(request)
    
    context = {
        'form': form,
        'payment_method': payment_method,
        'action': 'Edit',
        **cart_context,
    }
    return render(request, 'storefront/account_payment_form.html', context)


@login_required
@require_POST
def account_payment_delete(request, payment_id):
    """Delete a payment method."""
    payment_method = get_object_or_404(SavedPaymentMethod, id=payment_id, user=request.user)
    payment_method.delete()
    messages.success(request, 'Payment method deleted successfully!')
    return redirect('account_payment_methods')


@login_required
def account_reviews(request):
    """My Reviews page - show all reviews by the user."""
    product_reviews = ProductReview.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    delivery_reviews = DeliveryServiceReview.objects.filter(user=request.user).select_related('order').order_by('-created_at')
    
    cart_context = get_cart_context(request)
    
    context = {
        'product_reviews': product_reviews,
        'delivery_reviews': delivery_reviews,
        **cart_context,
    }
    return render(request, 'storefront/account_reviews.html', context)


@login_required
def account_returns(request):
    """My Returns page - show return requests."""
    # For now, return empty list - can be extended later
    returns = []
    
    cart_context = get_cart_context(request)
    
    context = {
        'returns': returns,
        **cart_context,
    }
    return render(request, 'storefront/account_returns.html', context)


@login_required
def account_cancellations(request):
    """My Cancellations page - show cancelled orders."""
    # For now, return empty list - can be extended later
    cancellations = []
    
    cart_context = get_cart_context(request)
    
    context = {
        'cancellations': cancellations,
        **cart_context,
    }
    return render(request, 'storefront/account_cancellations.html', context)

# --- Return/Refund Views ---

@login_required
def return_type_selection(request, order_id):
    """First step: User selects return type (not received vs not satisfied)."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        if form.is_valid():
            return_type = form.cleaned_data['return_type']
            # Store return_type in session and redirect to return request page
            request.session['return_type'] = return_type
            request.session['return_order_id'] = order_id
            return redirect('return_request', order_id=order_id)
    else:
        form = ReturnRequestForm()
    
    cart_context = get_cart_context(request)
    
    context = {
        'order': order,
        'form': form,
        **cart_context,
    }
    return render(request, 'storefront/return_type_selection.html', context)

@login_required
def return_request(request, order_id):
    """Main return request page where user selects items and provides details."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    # Get return_type from session
    return_type = request.session.get('return_type')
    if not return_type:
        # If no return_type in session, redirect to selection page
        return redirect('return_type_selection', order_id=order_id)
    
    # Get items already in return request (if editing)
    return_request_id = request.GET.get('return_request_id')
    existing_items = []
    if return_request_id:
        try:
            existing_return = ReturnRequest.objects.get(id=return_request_id, user=request.user, order=order)
            existing_items = [item.order_item.id for item in existing_return.items.all()]
        except ReturnRequest.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Handle adding items to return
        if 'add_item' in request.POST:
            order_item_id = int(request.POST.get('order_item_id'))
            order_item = get_object_or_404(OrderItem, id=order_item_id, order=order)
            
            form = ReturnItemForm(request.POST, request.FILES)
            if form.is_valid():
                # Store item data in session for later processing
                if 'return_items' not in request.session:
                    request.session['return_items'] = []
                
                item_data = {
                    'order_item_id': order_item_id,
                    'quantity': form.cleaned_data['quantity'],
                    'refund_reason': form.cleaned_data['refund_reason'],
                    'additional_comments': form.cleaned_data['additional_comments'],
                }
                
                # Handle image upload
                if 'image' in request.FILES:
                    from django.core.files.storage import default_storage
                    image = request.FILES['image']
                    file_path = default_storage.save(f'returns/temp_{request.user.id}_{order_item_id}_{image.name}', image)
                    item_data['image_path'] = file_path
                
                request.session['return_items'].append(item_data)
                request.session.modified = True
                messages.success(request, f'Added {order_item.product.name} to return request.')
                return redirect('return_request', order_id=order_id)
        
        # Handle final submission
        elif 'submit_return' in request.POST:
            submission_form = ReturnRequestSubmissionForm(request.POST)
            if submission_form.is_valid():
                return_items = request.session.get('return_items', [])
                if not return_items:
                    messages.error(request, 'Please add at least one item to return.')
                    return redirect('return_request', order_id=order_id)
                
                # Combine additional comments from all items
                all_comments = []
                for item_data in return_items:
                    if item_data.get('additional_comments'):
                        all_comments.append(item_data['additional_comments'])
                
                # Create return request
                return_request_obj = ReturnRequest.objects.create(
                    order=order,
                    user=request.user,
                    return_type=return_type,
                    refund_reason=return_items[0]['refund_reason'],  # Use first item's reason as primary
                    additional_comments='\n\n'.join(all_comments) if all_comments else '',
                    refund_method=submission_form.cleaned_data['refund_method'],
                    accepted_policy=submission_form.cleaned_data['accepted_policy'],
                )
                
                # Create return request items
                for item_data in return_items:
                    order_item = get_object_or_404(OrderItem, id=item_data['order_item_id'], order=order)
                    
                    return_item = ReturnRequestItem.objects.create(
                        return_request=return_request_obj,
                        order_item=order_item,
                        quantity=item_data['quantity'],
                    )
                    
                    # Move uploaded image from temp to final location
                    if 'image_path' in item_data:
                        from django.core.files.storage import default_storage
                        from django.core.files.base import ContentFile
                        import os
                        
                        temp_path = item_data['image_path']
                        if default_storage.exists(temp_path):
                            with default_storage.open(temp_path, 'rb') as f:
                                file_content = f.read()
                                file_name = os.path.basename(temp_path).replace('temp_', '')
                                return_item.image.save(file_name, ContentFile(file_content), save=True)
                            default_storage.delete(temp_path)
                
                # Clear session data
                del request.session['return_type']
                del request.session['return_order_id']
                del request.session['return_items']
                request.session.modified = True
                
                messages.success(request, 'Return request submitted successfully! Refund will be processed in 5-7 business days.')
                return redirect('order_detail', order_id=order_id)
    
    # Get items in session
    return_items = request.session.get('return_items', [])
    return_item_ids = [item['order_item_id'] for item in return_items]
    
    # Prepare forms for each order item
    item_forms = []
    for item in order_items:
        # Check if item is already in return request
        existing_data = next((i for i in return_items if i['order_item_id'] == item.id), None)
        if existing_data:
            form = ReturnItemForm(initial={
                'order_item_id': item.id,
                'quantity': existing_data['quantity'],
                'refund_reason': existing_data['refund_reason'],
                'additional_comments': existing_data['additional_comments'],
            })
        else:
            form = ReturnItemForm(initial={
                'order_item_id': item.id,
                'quantity': item.quantity,
            })
        item_forms.append((item, form))
    
    submission_form = ReturnRequestSubmissionForm()
    
    cart_context = get_cart_context(request)
    
    context = {
        'order': order,
        'order_items': order_items,
        'item_forms': item_forms,
        'return_items': return_items,
        'return_item_ids': return_item_ids,
        'submission_form': submission_form,
        'return_type': return_type,
        **cart_context,
    }
    return render(request, 'storefront/return_request.html', context)

@login_required
def remove_return_item(request, order_id, item_index):
    """Remove an item from the return request session."""
    return_items = request.session.get('return_items', [])
    if 0 <= item_index < len(return_items):
        # Delete associated image if exists
        item_data = return_items[item_index]
        if 'image_path' in item_data:
            from django.core.files.storage import default_storage
            if default_storage.exists(item_data['image_path']):
                default_storage.delete(item_data['image_path'])
        
        return_items.pop(item_index)
        request.session['return_items'] = return_items
        request.session.modified = True
        messages.success(request, 'Item removed from return request.')
    
    return redirect('return_request', order_id=order_id)

@login_required
def buy_again(request, order_id):
    """Add all items from a previous order back to the cart."""
    from adminpanel.models import Order, OrderItem
    from .cart_helpers import get_or_create_cart, add_product_to_cart
    
    # Get order and verify it belongs to the user
    try:
        customer = Customer.objects.get(user=request.user)
        order = get_object_or_404(Order, id=order_id, customer=customer)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('my_orders')
    
    # Get all order items
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    
    if not order_items.exists():
        messages.error(request, 'This order has no items.')
        return redirect('my_orders')
    
    # Add items to cart
    cart = get_or_create_cart(request)
    added_count = 0
    skipped_count = 0
    skipped_items = []
    
    for order_item in order_items:
        product = order_item.product
        
        # Check if product is still available
        if product.quantity_on_hand <= 0:
            skipped_count += 1
            skipped_items.append(product.name)
            continue
        
        # Add to cart (use original quantity, but cap at current stock)
        quantity_to_add = min(order_item.quantity, product.quantity_on_hand)
        success, message, cart_item, cart_total = add_product_to_cart(cart, product.id, quantity_to_add)
        
        if success:
            added_count += 1
        else:
            skipped_count += 1
            skipped_items.append(product.name)
    
    # Show appropriate messages
    if added_count > 0:
        if skipped_count > 0:
            messages.warning(
                request, 
                f'{added_count} item(s) added to cart. {skipped_count} item(s) could not be added (out of stock or unavailable).'
            )
        else:
            messages.success(request, f'All {added_count} item(s) from this order have been added to your cart.')
    else:
        messages.error(request, 'No items could be added to cart. All items may be out of stock.')
    
    return redirect('shopping_cart')

@login_required
def buy_again_item(request, order_id, item_id):
    """Add a single item from a previous order back to the cart."""
    from adminpanel.models import Order, OrderItem
    from .cart_helpers import get_or_create_cart, add_product_to_cart
    
    # Get order and verify it belongs to the user
    try:
        customer = Customer.objects.get(user=request.user)
        order = get_object_or_404(Order, id=order_id, customer=customer)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('my_orders')
    
    # Get the specific order item
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    product = order_item.product
    
    # Check if product is still available
    if product.quantity_on_hand <= 0:
        messages.error(request, f'{product.name} is currently out of stock.')
        return redirect('order_detail', order_id=order_id)
    
    # Add to cart (use original quantity, but cap at current stock)
    cart = get_or_create_cart(request)
    quantity_to_add = min(order_item.quantity, product.quantity_on_hand)
    success, message, cart_item, cart_total = add_product_to_cart(cart, product.id, quantity_to_add)
    
    if success:
        messages.success(request, f'{product.name} added to cart.')
    else:
        messages.error(request, message)
    
    return redirect('order_detail', order_id=order_id)