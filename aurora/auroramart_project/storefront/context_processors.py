from .models import Category, SubCategory
from adminpanel.models import Customer, Order, OrderItem, Product
from .forms import CustomerProfileForm
from datetime import date
from django.db.models import Count, Q

def get_predicted_subcategories(request, limit=5):
    """Get predicted preferred subcategories for the user based on order history, wishlist, or popular subcategories."""
    predicted_subcategories = []
    
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            
            # Get subcategories from user's order history
            orders = Order.objects.filter(customer=customer)
            order_items = OrderItem.objects.filter(order__in=orders).select_related('product')
            
            # Count subcategories from ordered products
            subcategory_counts = {}
            for item in order_items:
                if item.product.subcategory:
                    subcategory_counts[item.product.subcategory] = subcategory_counts.get(item.product.subcategory, 0) + item.quantity
            
            # Get subcategories from wishlist
            from .models import Wishlist, WishlistItem
            try:
                wishlist = Wishlist.objects.get(user=request.user)
                wishlist_items = WishlistItem.objects.filter(wishlist=wishlist).select_related('product')
                for item in wishlist_items:
                    if item.product.subcategory:
                        subcategory_counts[item.product.subcategory] = subcategory_counts.get(item.product.subcategory, 0) + 1
            except:
                pass
            
            # Sort by count and get top subcategories
            sorted_subcategories = sorted(subcategory_counts.items(), key=lambda x: x[1], reverse=True)
            predicted_subcategories = [name for name, count in sorted_subcategories[:limit]]
            
            # If we don't have enough, fill with popular subcategories
            if len(predicted_subcategories) < limit:
                popular_subcategories = Product.objects.filter(
                    quantity_on_hand__gt=0,
                    subcategory__isnull=False
                ).exclude(
                    subcategory__in=predicted_subcategories
                ).values('subcategory').annotate(
                    count=Count('id')
                ).order_by('-count')[:limit - len(predicted_subcategories)]
                
                for item in popular_subcategories:
                    if item['subcategory'] and item['subcategory'] not in predicted_subcategories:
                        predicted_subcategories.append(item['subcategory'])
        except Customer.DoesNotExist:
            pass
    
    # If no user or not enough subcategories, use popular subcategories
    if len(predicted_subcategories) < limit:
        popular_subcategories = Product.objects.filter(
            quantity_on_hand__gt=0,
            subcategory__isnull=False
        ).exclude(
            subcategory__in=predicted_subcategories
        ).values('subcategory').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        for item in popular_subcategories:
            if item['subcategory'] and item['subcategory'] not in predicted_subcategories:
                predicted_subcategories.append(item['subcategory'])
    
    return predicted_subcategories[:limit]

def categories(request):
    """Make categories with subcategories available to all templates."""
    # Get all active categories and their active subcategories
    categories_list = []
    for category in Category.objects.filter(is_active=True).order_by('name'):
        subcategories = category.subcategories.filter(is_active=True).order_by('name')
        categories_list.append({
            'category': category,
            'subcategories': subcategories
        })
    
    # Get predicted subcategories for animated search placeholder
    predicted_subcategories = get_predicted_subcategories(request, limit=5)
    
    context = {
        'navigation_categories': categories_list,
        'predicted_subcategories': predicted_subcategories
    }
    
    # Check if profile onboarding modal should be shown
    show_profile_modal = False
    profile_form = None
    
    if request.user.is_authenticated:
        # Check if URL has show_onboarding parameter
        if request.GET.get('show_onboarding') == 'true':
            # Check if customer profile is incomplete
            try:
                customer = Customer.objects.get(user=request.user)
                if not customer.age or not customer.gender or not customer.employment_status:
                    show_profile_modal = True
                    # Check if there's form data in session (from failed submission)
                    if 'profile_form_data' in request.session:
                        form_data = request.session.pop('profile_form_data')
                        profile_form = CustomerProfileForm(data=form_data)
                        # Clear the error flag
                        request.session.pop('profile_form_errors', None)
                    else:
                        # Create form for modal
                        profile_form = CustomerProfileForm()
                        # Pre-fill if customer exists
                        if customer.age:
                            approximate_dob = date(date.today().year - customer.age, 1, 1)
                            profile_form = CustomerProfileForm(initial={
                                'date_of_birth': approximate_dob,
                                'gender': customer.gender,
                                'employment_status': customer.employment_status,
                                'occupation': customer.occupation,
                                'education': customer.education,
                                'household_size': customer.household_size,
                                'has_children': customer.has_children,
                                'monthly_income_sgd': customer.monthly_income_sgd,
                            })
            except Customer.DoesNotExist:
                show_profile_modal = True
                # Check if there's form data in session (from failed submission)
                if 'profile_form_data' in request.session:
                    form_data = request.session.pop('profile_form_data')
                    profile_form = CustomerProfileForm(data=form_data)
                    request.session.pop('profile_form_errors', None)
                else:
                    profile_form = CustomerProfileForm()
    
    context['show_profile_modal'] = show_profile_modal
    context['profile_form'] = profile_form
    
    return context

