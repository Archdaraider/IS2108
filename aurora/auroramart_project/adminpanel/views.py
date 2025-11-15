import joblib
import os
import json
import pandas as pd
from decimal import Decimal
from django.db.models import Count, Sum, F, DecimalField, Avg, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .models import Customer, Product, Order, OrderItem, DecisionTreeModel
from django.db import models
from .forms import CustomerForm, ProductForm, OrderForm, OrderItemForm, OrderItemFormSet # Ensure OrderItemFormSet is imported
from django.http import HttpResponseNotAllowed
from django.apps import apps
from django.db import transaction # Keep transaction import
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from .forms import AdminUserForm

# --- Load Models Once ---
app_path = apps.get_app_config('adminpanel').path

# Load the CUSTOMER classification model
model_path = os.path.join(app_path, 'mlmodels', 'b2c_customers_100.joblib')
try:
    customer_model = joblib.load(model_path)
except FileNotFoundError:
    customer_model = None
    print("WARNING: Customer model file not found.")

# Load the PRODUCT association rules (optional ML feature)
rules_path = os.path.join(app_path, 'mlmodels', 'b2c_products_500_transactions_50k.joblib')
try:
    product_rules = joblib.load(rules_path)
except FileNotFoundError:
    product_rules = None
    # Silently use fallback recommendations - this is expected if ML model not trained

# --- Authentication Views ---

class AdminLoginView(LoginView):
    """Custom login view for the admin panel."""
    template_name = 'adminpanel/login.html'
    next_page = 'adminpanel:admin_dashboard_home'

def admin_logout_view(request):
    """
    Custom logout view that logs out the user and renders a template.
    Does not redirect, unlike Django's default LogoutView.
    """
    logout(request)
    return render(request, 'adminpanel/logout.html')
    
def customer_landing_page(request):
    """
    Redirects to the customer-facing storefront homepage.
    """
    from django.shortcuts import redirect
    return redirect('homepage')  # Redirect to storefront homepage
# --- Core Dashboard View ---

@login_required(login_url='adminpanel:admin_login')
def admin_dashboard_home(request):
    """
    Main Dashboard View - Gathers KPIs and initial data for index.html.
    """
    # Filter to exclude admin/staff users from customer counts
    real_customers = Customer.objects.filter(
        models.Q(user__isnull=True) | models.Q(user__is_staff=False)
    )
    
    kpis = {
        'total_customers': real_customers.count(),
        'total_products': Product.objects.count(),
        'active_models': DecisionTreeModel.objects.filter(is_active=True).count(),
        'total_transactions': Order.objects.count(),
    }

    inventory_alerts = Product.objects.filter(
        quantity_on_hand__lte=models.F('reorder_quantity')
    ).order_by('quantity_on_hand')[:10]

    # Get all preferred categories for pie chart (not just top 5) - exclude admin users
    category_data = real_customers.values('preferred_category') \
        .annotate(count=Count('id')) \
        .order_by('-count')
    
    # Prepare data for Chart.js pie chart (convert to JSON strings for template)
    pie_chart_labels = [item['preferred_category'] for item in category_data]
    pie_chart_counts = [item['count'] for item in category_data]
    
    pie_chart_data = {
        'labels': json.dumps(pie_chart_labels),
        'counts': json.dumps(pie_chart_counts),
    }
    
    # Keep the list version for backwards compatibility if needed
    segment_summary = list(category_data[:5])

    # Customer Summary Statistics (exclude admin users)
    # Get aggregate statistics: total orders, average order value, last order date
    customer_summary = real_customers.annotate(
        total_orders=Count('order', distinct=True),
        avg_order_value=Avg('order__total_amount'),
        last_order_date=Max('order__placed_at')
    ).order_by('-total_orders')[:10]  # Top 10 customers by order count
    
    # Calculate overall statistics (exclude admin users)
    overall_stats = {
        'total_customers_with_orders': real_customers.filter(order__isnull=False).distinct().count(),
        'avg_order_value_all': Order.objects.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00'),
        'total_revenue': Order.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
    }

    # Top 3 and Worst 3 Rated Products
    top_rated_products = Product.objects.order_by('-rating', 'name')[:3]
    worst_rated_products = Product.objects.order_by('rating', 'name')[:3]

    model_status = DecisionTreeModel.objects.order_by('-training_date')
    
    # Get sales data for the last 6 months (real data)
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    six_months_ago = timezone.now() - timedelta(days=180)
    
    monthly_sales = Order.objects.filter(
        placed_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('placed_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    # Prepare sales chart data
    sales_labels = []
    sales_values = []
    
    if monthly_sales.exists():
        for item in monthly_sales:
            month_name = item['month'].strftime('%b')
            sales_labels.append(month_name)
            sales_values.append(float(item['total'] or 0))
    else:
        # If no orders, show empty chart
        sales_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        sales_values = [0, 0, 0, 0, 0, 0]
    
    sales_chart_data = {
        'labels': json.dumps(sales_labels),
        'values': json.dumps(sales_values),
    }

    context = {
        'page_title': 'Dashboard',
        'kpis': kpis,
        'inventory_alerts': inventory_alerts,
        'segment_summary': segment_summary,
        'pie_chart_data': pie_chart_data,
        'sales_chart_data': sales_chart_data,
        'customer_summary': customer_summary,
        'overall_stats': overall_stats,
        'top_rated_products': top_rated_products,
        'worst_rated_products': worst_rated_products,
        'model_status': model_status,
    }

    return render(request, 'adminpanel/index.html', context)


# --- Product List/Create/Detail/Delete Views ---

@login_required(login_url='adminpanel:admin_login')
def product_list(request):
    """View to LIST and CREATE Products on one page with sorting and filtering."""
    # Get all products for filtering/sorting
    products = Product.objects.all()
    
    # Handle filtering
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    subcategory_filter = request.GET.get('subcategory', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    rating_min = request.GET.get('rating_min', '')
    stock_filter = request.GET.get('stock', '')
    
    if search_query:
        products = products.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(sku__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category=category_filter)
    
    if subcategory_filter:
        products = products.filter(subcategory=subcategory_filter)
    
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)
    
    if rating_min:
        products = products.filter(rating__gte=rating_min)
    
    if stock_filter == 'low':
        products = products.filter(quantity_on_hand__lte=models.F('reorder_quantity'))
    elif stock_filter == 'out':
        products = products.filter(quantity_on_hand=0)
    elif stock_filter == 'in_stock':
        products = products.filter(quantity_on_hand__gt=0)
    
    # Handle sorting
    sort_by = request.GET.get('sort', '-id')  # Default sort by newest first
    valid_sort_fields = ['id', '-id', 'name', '-name', 'sku', '-sku', 'price', '-price', 
                        'rating', '-rating', 'quantity_on_hand', '-quantity_on_hand', 
                        'category', '-category', 'subcategory', '-subcategory']
    
    if sort_by in valid_sort_fields:
        products = products.order_by(sort_by)
    else:
        products = products.order_by('-id')
    
    # Handle form submission for creating new products
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:product_list')
    else:
        form = ProductForm()

    # Get unique categories and subcategories for filter dropdowns
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')
    subcategories = Product.objects.values_list('subcategory', flat=True).distinct().order_by('subcategory')

    context = {
        'page_title': 'Product List',
        'products': products,
        'form': form,
        'search_query': search_query,
        'category_filter': category_filter,
        'subcategory_filter': subcategory_filter,
        'price_min': price_min,
        'price_max': price_max,
        'rating_min': rating_min,
        'stock_filter': stock_filter,
        'sort_by': sort_by,
        'categories': categories,
        'subcategories': subcategories,
    }
    return render(request, 'adminpanel/product_list.html', context)

@login_required(login_url='adminpanel:admin_login')
def product_detail(request, pk):
    """View to display and update a single product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    context = {
        'page_title': f'Edit {product.name}',
        'form': form,
        'product': product
    }
    return render(request, 'adminpanel/product_detail.html', context)

@login_required(login_url='adminpanel:admin_login')
def product_delete(request, pk):
    """View to delete a single product."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('adminpanel:product_list')


# --- Order List/Create/Detail/Delete Views ---

@login_required(login_url='adminpanel:admin_login')
def order_list(request):
    """View to LIST and CREATE Orders, now with OrderItems, sorting and filtering."""
    # Get all orders for filtering/sorting
    orders = Order.objects.all()
    
    # Handle filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    amount_min = request.GET.get('amount_min', '')
    amount_max = request.GET.get('amount_max', '')
    
    if search_query:
        orders = orders.filter(
            models.Q(oID__icontains=search_query) |
            models.Q(customer__name__icontains=search_query) |
            models.Q(customer__email__icontains=search_query) |
            models.Q(shipping_address__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(fulfillment_status=status_filter)
    
    if customer_filter:
        orders = orders.filter(customer__id=customer_filter)
    
    if date_from:
        orders = orders.filter(placed_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(placed_at__date__lte=date_to)
    
    if amount_min:
        orders = orders.filter(total_amount__gte=amount_min)
    if amount_max:
        orders = orders.filter(total_amount__lte=amount_max)
    
    # Handle sorting
    sort_by = request.GET.get('sort', '-placed_at')  # Default sort by newest first
    valid_sort_fields = ['id', '-id', 'placed_at', '-placed_at', 'total_amount', '-total_amount', 
                        'fulfillment_status', '-fulfillment_status', 'customer__name', '-customer__name']
    
    if sort_by in valid_sort_fields:
        orders = orders.order_by(sort_by)
    else:
        orders = orders.order_by('-placed_at')
    
    # Limit to 100 orders for performance
    orders = orders[:100]

    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST) # Use the imported formset

        if form.is_valid() and formset.is_valid():
             # Use a transaction to ensure atomicity
            with transaction.atomic():
                # 1. Save the parent Order first to get an ID
                order = form.save()

                # 2. Iterate and save items, setting unit_price manually
                items_to_save = formset.save(commit=False)
                total_amount = Decimal('0.00')

                for item in items_to_save:
                    # Only save if a product was selected (and it's not a deletion of an existing item)
                    # NOTE: item.product is guaranteed to be non-None if formset.is_valid() passed and the row was filled
                    if item.product and item.quantity:
                        item.order = order
                        # 🔑 CRITICAL FIX: Ensure unit_price is explicitly set from the Product before saving
                        item.unit_price = item.product.price
                        
                        # Add to the total (ensure Decimal calculation)
                        total_amount += (item.unit_price * Decimal(item.quantity))
                        item.save() # Save each item individually
                
                # Save m2m data (usually not needed for inline formsets but good practice)
                formset.save_m2m()

                # 3. Now update the order's total and save again
                order.total_amount = total_amount
                order.save(update_fields=['total_amount'])

                return redirect('adminpanel:order_list')
        # If form or formset is invalid, it will fall through to render the context below

    else: # GET request
        form = OrderForm()
        # Create an empty formset for a new order with 1 empty form
        formset = OrderItemFormSet(queryset=OrderItem.objects.none(), initial=[{'quantity': 1}])

    # Get unique customers and statuses for filter dropdowns
    customers = Customer.objects.all().order_by('name')
    statuses = Order.STATUS_CHOICES

    context = {
        'page_title': 'Order List',
        'orders': orders,
        'form': form,
        'formset': formset, # Pass the formset to the template
        'search_query': search_query,
        'status_filter': status_filter,
        'customer_filter': customer_filter,
        'date_from': date_from,
        'date_to': date_to,
        'amount_min': amount_min,
        'amount_max': amount_max,
        'sort_by': sort_by,
        'customers': customers,
        'statuses': statuses,
    }
    return render(request, 'adminpanel/order_list.html', context)

# ---
# FIXED `order_detail` VIEW
# ---
@login_required(login_url='adminpanel:admin_login')
def order_detail(request, pk):
    """
    View to display and update a single order and its items.
    Completely rewritten with manual DELETE handling.
    """
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the order form
                    order = form.save()
                    
                    # Get the total number of forms
                    total_forms = int(request.POST.get('items-TOTAL_FORMS', 0))
                    
                    # Track items to delete and items to keep
                    items_to_delete = []
                    items_to_save = []
                    
                    # Process each form manually
                    for i in range(total_forms):
                        # Check if this form has DELETE checked
                        delete_key = f'items-{i}-DELETE'
                        is_marked_for_deletion = delete_key in request.POST
                        
                        # Get the item ID (if it exists)
                        item_id = request.POST.get(f'items-{i}-id', '')
                        
                        # Get product and quantity
                        product_id = request.POST.get(f'items-{i}-product', '')
                        quantity = request.POST.get(f'items-{i}-quantity', '')
                        
                        if is_marked_for_deletion and item_id:
                            # Mark existing item for deletion
                            items_to_delete.append(item_id)
                        elif product_id and quantity:
                            # This item should be saved
                            items_to_save.append({
                                'id': item_id if item_id else None,
                                'product_id': product_id,
                                'quantity': quantity
                            })
                    
                    # Delete marked items
                    for item_id in items_to_delete:
                        try:
                            item = OrderItem.objects.get(pk=item_id, order=order)
                            item.delete()
                        except OrderItem.DoesNotExist:
                            pass
                    
                    # Save/update remaining items
                    for item_data in items_to_save:
                        try:
                            product = Product.objects.get(pk=item_data['product_id'])
                            quantity = int(item_data['quantity'])
                            
                            if item_data['id']:
                                # Update existing item
                                item = OrderItem.objects.get(pk=item_data['id'], order=order)
                                item.product = product
                                item.quantity = quantity
                                item.unit_price = product.price
                                item.save()
                            else:
                                # Create new item
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity,
                                    unit_price=product.price
                                )
                        except (Product.DoesNotExist, OrderItem.DoesNotExist):
                            pass
                    
                    # Recalculate order total
                    total_result = order.items.aggregate(
                        total=Sum(F('unit_price') * F('quantity'), output_field=DecimalField())
                    )
                    order.total_amount = total_result['total'] or Decimal('0.00')
                    order.save(update_fields=['total_amount'])

                    return redirect('adminpanel:order_detail', pk=order.pk)

            except Exception as e:
                form.add_error(None, f"An error occurred while saving: {str(e)}")
            
    else:
        # GET request - display the form
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)

    context = {
        'page_title': f'Edit Order {order.oID}',
        'form': form,
        'formset': formset,
        'order': order
    }
    return render(request, 'adminpanel/order_detail.html', context)
# ---
# END OF FIXED VIEW
# ---

@login_required(login_url='adminpanel:admin_login')
def order_delete(request, pk):
    """View to delete a single order (the entire order)."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return redirect('adminpanel:order_list')


# --- Catalogue Management Views ---

@login_required(login_url='adminpanel:admin_login')
def catalogue_view(request):
    """
    Catalogue page for managing product visibility on the storefront.
    Displays all products in a grid layout with toggle switches.
    """
    # Get all products
    products = Product.objects.all().order_by('-id')
    
    # Handle filtering
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')  # 'active', 'inactive', or ''
    search_query = request.GET.get('search', '')
    
    if search_query:
        products = products.filter(
            models.Q(name__icontains=search_query) |
            models.Q(sku__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category=category_filter)
    
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    
    # Get unique categories for filter dropdown
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')
    
    # Statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = Product.objects.filter(is_active=False).count()
    
    context = {
        'page_title': 'Catalogue',
        'products': products,
        'categories': categories,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
    }
    
    return render(request, 'adminpanel/catalogue.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def catalogue_toggle_active(request, pk):
    """
    AJAX endpoint to toggle product visibility.
    Returns JSON response.
    """
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save(update_fields=['is_active'])
        
        return JsonResponse({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def catalogue_bulk_update(request):
    """
    Handle bulk show/hide actions for multiple products.
    Expects POST data: {'action': 'activate'|'deactivate', 'product_ids': [1, 2, 3]}
    """
    try:
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if action not in ['activate', 'deactivate']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action. Must be "activate" or "deactivate".'
            }, status=400)
        
        if not product_ids:
            return JsonResponse({
                'success': False,
                'error': 'No products selected.'
            }, status=400)
        
        # Convert to integers and filter products
        product_ids = [int(pid) for pid in product_ids]
        products = Product.objects.filter(pk__in=product_ids)
        
        # Update products
        new_status = (action == 'activate')
        updated_count = products.update(is_active=new_status)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Successfully {action}d {updated_count} product(s).'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# --- Customer Views (Unchanged) ---
@login_required(login_url='adminpanel:admin_login')
def customer_list(request):
    """
    Handles LISTING customers and CREATING new ones with AI prediction.
    Now includes sorting and filtering functionality.
    """
    # Get all customers for filtering/sorting (exclude admin/staff users)
    customers = Customer.objects.filter(
        models.Q(user__isnull=True) | models.Q(user__is_staff=False)
    )
    
    # Handle filtering
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    age_min = request.GET.get('age_min', '')
    age_max = request.GET.get('age_max', '')
    income_min = request.GET.get('income_min', '')
    income_max = request.GET.get('income_max', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        customers = customers.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(email__icontains=search_query)
        )
    
    if category_filter:
        customers = customers.filter(preferred_category=category_filter)
    
    if status_filter:
        if status_filter == 'active':
            customers = customers.filter(user__isnull=False, user__is_active=True)
        elif status_filter == 'inactive':
            customers = customers.filter(user__isnull=False, user__is_active=False)
        elif status_filter == 'no_account':
            customers = customers.filter(user__isnull=True)
    
    if age_min:
        customers = customers.filter(age__gte=age_min)
    if age_max:
        customers = customers.filter(age__lte=age_max)
    
    if income_min:
        customers = customers.filter(monthly_income_sgd__gte=income_min)
    if income_max:
        customers = customers.filter(monthly_income_sgd__lte=income_max)
    
    # Handle sorting
    sort_by = request.GET.get('sort', '-id')  # Default sort by newest first
    valid_sort_fields = ['id', '-id', 'name', '-name', 'email', '-email', 'age', '-age', 
                        'monthly_income_sgd', '-monthly_income_sgd', 'preferred_category', '-preferred_category']
    
    if sort_by in valid_sort_fields:
        customers = customers.order_by(sort_by)
    else:
        customers = customers.order_by('-id')
    
    # Handle form submission for creating new customers
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            # Debug: Print form data to verify all fields are present
            print("DEBUG: Form cleaned_data:", form.cleaned_data)
            print("DEBUG: POST data:", request.POST)
            # Create User account first
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            email = form.cleaned_data.get('email')
            
            try:
                # Create the User account
                # NOTE: A signal in storefront/signals.py will automatically create a Customer
                # with placeholder values. We'll update that Customer with the real form data.
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Check if signal already created a customer (it will have placeholder values)
                # If it exists, update it; otherwise create a new one
                customer, created = Customer.objects.get_or_create(
                    email=email,
                    defaults={
                        'user': user,
                        'name': form.cleaned_data.get('name'),
                        'age': form.cleaned_data.get('age'),
                        'gender': form.cleaned_data.get('gender'),
                        'employment_status': form.cleaned_data.get('employment_status'),
                        'occupation': form.cleaned_data.get('occupation'),
                        'education': form.cleaned_data.get('education'),
                        'household_size': form.cleaned_data.get('household_size'),
                        'has_children': form.cleaned_data.get('has_children', False),
                        'monthly_income_sgd': form.cleaned_data.get('monthly_income_sgd'),
                    }
                )
                
                # If customer already exists (created by signal), update all fields with form data
                if not created:
                    # Verify all required fields are present
                    required_fields = ['email', 'name', 'age', 'gender', 'employment_status', 
                                      'occupation', 'education', 'household_size', 'monthly_income_sgd']
                    missing_fields = [field for field in required_fields 
                                     if form.cleaned_data.get(field) is None]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {missing_fields}. Form data: {form.cleaned_data}")
                    
                    customer.user = user
                    customer.email = form.cleaned_data.get('email')
                    customer.name = form.cleaned_data.get('name')
                    customer.age = form.cleaned_data.get('age')
                    customer.gender = form.cleaned_data.get('gender')
                    customer.employment_status = form.cleaned_data.get('employment_status')
                    customer.occupation = form.cleaned_data.get('occupation')
                    customer.education = form.cleaned_data.get('education')
                    customer.household_size = form.cleaned_data.get('household_size')
                    customer.has_children = form.cleaned_data.get('has_children', False)
                    customer.monthly_income_sgd = form.cleaned_data.get('monthly_income_sgd')

                # --- AI MODEL LOGIC (matching your notebook) ---
                if customer_model: # Only check for the model
                    try:
                        # 1. Define the full list of 22 features your model was trained on
                        TRAINING_COLUMNS = [
                            'age', 'household_size', 'has_children', 'monthly_income_sgd',
                            'gender_Female', 'gender_Male', 'employment_status_Full-time',
                            'employment_status_Part-time', 'employment_status_Retired',
                            'employment_status_Self-employed', 'employment_status_Student',
                            'occupation_Admin', 'occupation_Education', 'occupation_Sales',
                            'occupation_Service', 'occupation_Skilled Trades', 'occupation_Tech',
                            'education_Bachelor', 'education_Diploma', 'education_Doctorate',
                            'education_Master', 'education_Secondary'
                        ]

                        # 2. Create a dictionary of the *raw* features from the form
                        raw_data = {
                            'age': form.cleaned_data.get('age'),
                            'household_size': form.cleaned_data.get('household_size'),
                            'has_children': form.cleaned_data.get('has_children', False),
                            'monthly_income_sgd': form.cleaned_data.get('monthly_income_sgd'),
                            'gender': form.cleaned_data.get('gender'),
                            'employment_status': form.cleaned_data.get('employment_status'),
                            'occupation': form.cleaned_data.get('occupation'),
                            'education': form.cleaned_data.get('education')
                        }

                        # 3. Convert dictionary to a single-row pandas DataFrame
                        features_df = pd.DataFrame([raw_data])

                        # 4. One-hot encode the categorical variables (just like Cell 11 in your notebook)
                        features_encoded = pd.get_dummies(features_df, columns=['gender', 'employment_status', 'occupation', 'education'])

                        # 5. Add any missing columns that weren't in this input
                        for col in TRAINING_COLUMNS:
                            if col not in features_encoded.columns:
                                features_encoded[col] = 0 # 0 works for False/int

                        # 6. Reorder columns to *exactly* match the training data
                        features_processed = features_encoded[TRAINING_COLUMNS]

                        # 7. Make prediction
                        predicted_category = customer_model.predict(features_processed)[0]

                        # 8. Assign prediction
                        customer.preferred_category = predicted_category

                    except Exception as e:
                        # If prediction fails, log it but continue
                        print(f"WARNING: Could not predict category: {e}")
                        # Set a default category if prediction fails
                        customer.preferred_category = 'Electronics'  # Default fallback
                
                # Save the customer with all fields explicitly set
                customer.save()
                return redirect('adminpanel:customer_list') # Success!
                
            except Exception as e:
                # If user creation fails, show error
                import traceback
                print(f"ERROR creating customer: {e}")
                print(traceback.format_exc())
                form.add_error(None, f"Could not create user account: {e}")
        else:
            # Form is invalid - print errors for debugging
            print("DEBUG: Form is invalid!")
            print("DEBUG: Form errors:", form.errors)
            print("DEBUG: Form non_field_errors:", form.non_field_errors)
            print("DEBUG: POST data:", request.POST)
            
        # If form is invalid, fall through to render context below

    else: # GET request
        form = CustomerForm() # An empty form

    # Get unique categories for filter dropdown
    categories = Customer.objects.values_list('preferred_category', flat=True).distinct().order_by('preferred_category')

    context = {
        'page_title': 'Customers',
        'customers': customers,
        'form': form,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'age_min': age_min,
        'age_max': age_max,
        'income_min': income_min,
        'income_max': income_max,
        'sort_by': sort_by,
        'categories': categories,
    }
    return render(request, 'adminpanel/customer_list.html', context)

@login_required(login_url='adminpanel:admin_login')
def customer_detail(request, pk):
    """
    Handles UPDATING an existing customer.
    """
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            # Update username and password if provided
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Create or update user account
            if username or password:
                if customer.user:
                    # Update existing user
                    if username:
                        customer.user.username = username
                    if password:
                        customer.user.set_password(password)
                    customer.user.save()
                else:
                    # Create new user if customer doesn't have one
                    if username and password:
                        user = User.objects.create_user(
                            username=username,
                            email=customer.email,
                            password=password
                        )
                        customer.user = user
            
            # Explicitly update all customer fields from form data to ensure they're saved
            customer.email = form.cleaned_data.get('email')
            customer.name = form.cleaned_data.get('name')
            customer.age = form.cleaned_data.get('age')
            customer.gender = form.cleaned_data.get('gender')
            customer.employment_status = form.cleaned_data.get('employment_status')
            customer.occupation = form.cleaned_data.get('occupation')
            customer.education = form.cleaned_data.get('education')
            customer.household_size = form.cleaned_data.get('household_size')
            customer.has_children = form.cleaned_data.get('has_children', False)
            customer.monthly_income_sgd = form.cleaned_data.get('monthly_income_sgd')
            
            # Save customer with all fields explicitly set
            customer.save()
            return redirect('adminpanel:customer_list') # Redirect to list after update
    else: # GET request
        form = CustomerForm(instance=customer)

    context = {
        'page_title': f'Edit {customer.name}',
        'form': form,
        'customer': customer
    }
    return render(request, 'adminpanel/customer_detail.html', context)


@login_required(login_url='adminpanel:admin_login')
def customer_delete(request, pk):
    """
    Handles the POST request to delete a customer.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('adminpanel:customer_list')


@login_required(login_url='adminpanel:admin_login')
def customer_toggle_active(request, pk):
    """
    Toggles the active status of a customer's user account.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    customer = get_object_or_404(Customer, pk=pk)
    
    # If customer has a user account, toggle its active status
    if customer.user:
        customer.user.is_active = not customer.user.is_active
        customer.user.save()
    else:
        # If no user account exists, create one with is_active=False
        # This allows you to create "inactive" customers
        pass
    
    return redirect('adminpanel:customer_list')


# --- Admin User Management Views ---

def superuser_required(user):
    """Check if user is a superuser."""
    return user.is_authenticated and user.is_superuser

@login_required(login_url='adminpanel:admin_login')
@user_passes_test(superuser_required, login_url='adminpanel:admin_login')
def admin_users_list(request):
    """
    List all admin users (staff users).
    Only accessible by superuser.
    """
    # Get all staff users (including superuser)
    admin_users = User.objects.filter(is_staff=True).order_by('-date_joined')
    
    # Separate superuser from regular staff
    superusers = admin_users.filter(is_superuser=True)
    regular_admins = admin_users.filter(is_superuser=False)
    
    # Handle form submission for creating new admin
    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:admin_users_list')
    else:
        form = AdminUserForm()
    
    context = {
        'page_title': 'Admin Users',
        'superusers': superusers,
        'regular_admins': regular_admins,
        'form': form,
    }
    
    return render(request, 'adminpanel/admin_users_list.html', context)


@login_required(login_url='adminpanel:admin_login')
@user_passes_test(superuser_required, login_url='adminpanel:admin_login')
@require_POST
def admin_user_delete(request, pk):
    """
    Delete an admin user.
    Only superuser can delete admin users.
    Prevents deleting the superuser itself.
    """
    user_to_delete = get_object_or_404(User, pk=pk)
    
    # Prevent deleting yourself
    if user_to_delete == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot delete your own account.'
        }, status=400)
    
    # Prevent deleting the main admin superuser
    if user_to_delete.username == 'admin' and user_to_delete.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Cannot delete the main admin account.'
        }, status=400)
    
    try:
        username = user_to_delete.username
        user_to_delete.delete()
        return JsonResponse({
            'success': True,
            'message': f'Admin user "{username}" deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

# --- AI/ML Studio View ---

@login_required(login_url='adminpanel:admin_login')
def ai_studio_home(request):
    """Dedicated page for deploying and monitoring AI/ML models."""
    models = DecisionTreeModel.objects.all()
    context = {'page_title': 'AI/ML Studio', 'models': models}
    return render(request, 'adminpanel/ai_studio_home.html', context)


# --- Chat Support Views ---

@login_required(login_url='adminpanel:admin_login')
def chat_list(request):
    """Display all customer chats for admin."""
    from .models import Chat
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    chats = Chat.objects.select_related('customer').prefetch_related('messages')
    
    if status_filter:
        chats = chats.filter(status=status_filter)
    
    if search:
        chats = chats.filter(
            models.Q(customer__name__icontains=search) |
            models.Q(customer__email__icontains=search) |
            models.Q(subject__icontains=search)
        )
    
    # Calculate total unread messages
    total_unread = sum(chat.unread_count_admin for chat in chats)
    
    context = {
        'page_title': 'Customer Chats',
        'chats': chats,
        'total_unread': total_unread,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'adminpanel/chat_list.html', context)


@login_required(login_url='adminpanel:admin_login')
def chat_detail(request, chat_id):
    """View and respond to a specific chat."""
    from .models import Chat, Message
    
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Mark all customer messages as read when admin views chat
    chat.messages.filter(is_from_customer=True, is_read=False).update(is_read=True)
    
    context = {
        'page_title': f'Chat #{chat.id} - {chat.customer.name}',
        'chat': chat,
        'messages': chat.messages.all(),
    }
    return render(request, 'adminpanel/chat_detail.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["POST"])
def admin_send_message(request, chat_id):
    """Admin sends a message in a chat."""
    from .models import Chat, Message
    
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        message_text = request.POST.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            message=message_text,
            is_from_customer=False,
            sender_name=f"Admin ({request.user.username})",
            is_read=False
        )
        
        # Update chat status and timestamp
        chat.status = 'IN_PROGRESS'
        chat.last_admin_reply = timezone.now()
        chat.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'text': message.message,
                'sender': message.sender_name,
                'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_from_customer': message.is_from_customer
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["GET"])
def admin_get_messages(request, chat_id):
    """Get messages for a chat (used by admin for polling)."""
    from .models import Chat
    
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Mark customer messages as read when admin fetches
        chat.messages.filter(is_from_customer=True, is_read=False).update(is_read=True)
        
        # Get all messages
        messages = []
        for msg in chat.messages.all():
            messages.append({
                'id': msg.id,
                'text': msg.message,
                'sender': msg.sender_name,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_from_customer': msg.is_from_customer
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages,
            'unread_count': chat.unread_count_admin
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["POST"])
def admin_update_chat_status(request, chat_id):
    """Update chat status (open/in_progress/closed)."""
    from .models import Chat
    
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        new_status = request.POST.get('status')
        
        if new_status not in ['OPEN', 'IN_PROGRESS', 'CLOSED']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        chat.status = new_status
        chat.save()
        
        return JsonResponse({'success': True, 'status': new_status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["POST"])
def chat_delete(request, chat_id):
    """Delete a single chat conversation."""
    from .models import Chat
    
    try:
        chat = get_object_or_404(Chat, id=chat_id)
        customer_name = chat.customer.name
        chat.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Chat with {customer_name} has been deleted'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["POST"])
def chat_bulk_delete(request):
    """Bulk delete multiple chats."""
    from .models import Chat
    
    try:
        chat_ids = request.POST.getlist('chat_ids[]')
        
        if not chat_ids:
            return JsonResponse({'success': False, 'error': 'No chats selected'}, status=400)
        
        # Delete selected chats
        deleted_count = Chat.objects.filter(id__in=chat_ids).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} chat(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def customer_get_messages(request, chat_id):
    """Get messages for a chat (used by customer for polling)."""
    from .models import Chat
    
    try:
        # Get chat (customer must own it if logged in, or match by session)
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Security: check if customer owns this chat
        if request.user.is_authenticated:
            try:
                from .models import Customer
                customer = Customer.objects.get(user=request.user)
                if chat.customer.id != customer.id:
                    # This is expected when localStorage has a chat ID from another user
                    # Return 200 with reset flag instead of 403 to avoid log noise
                    # The JavaScript will handle this gracefully
                    return JsonResponse({
                        'success': False, 
                        'error': 'Unauthorized',
                        'reset_chat': True  # Signal to frontend to reset chat state
                    }, status=200)
            except Customer.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Customer not found'}, status=403)
        
        # Mark admin messages as read
        chat.messages.filter(is_from_customer=False, is_read=False).update(is_read=True)
        
        # Get all messages
        messages = []
        for msg in chat.messages.all():
            messages.append({
                'id': msg.id,
                'text': msg.message,
                'sender': msg.sender_name,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_from_customer': msg.is_from_customer
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages,
            'unread_count': chat.unread_count_customer
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def customer_check_chat(request):
    """Check if customer has an existing active chat."""
    from .models import Chat, Customer
    
    try:
        chat_id = None
        
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                existing_chat = Chat.objects.filter(
                    customer=customer,
                    status__in=['OPEN', 'IN_PROGRESS']
                ).first()
                
                if existing_chat:
                    chat_id = existing_chat.id
            except Customer.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'has_chat': chat_id is not None,
            'chat_id': chat_id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def customer_send_message(request):
    """Customer sends a message (creates chat if doesn't exist)."""
    from .models import Chat, Message, Customer
    
    try:
        message_text = request.POST.get('message', '').strip()
        chat_id = request.POST.get('chat_id')
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)
        
        # Get or create customer
        customer = None
        customer_name = "Guest"
        
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                customer_name = customer.name or request.user.username
            except Customer.DoesNotExist:
                # Create customer if logged in but no customer record
                customer = Customer.objects.create(
                    user=request.user,
                    name=request.user.username,
                    email=request.user.email
                )
                customer_name = customer.name
        else:
            # For guest users, try to find by email or create anonymous
            email = request.POST.get('email', '').strip()
            if email:
                customer, created = Customer.objects.get_or_create(
                    email=email,
                    defaults={'name': request.POST.get('name', 'Guest')}
                )
                customer_name = customer.name
            else:
                # Create anonymous customer
                customer = Customer.objects.create(
                    name="Anonymous Customer",
                    email=f"guest_{timezone.now().timestamp()}@temp.com"
                )
                customer_name = "Guest"
        
        # Get or create chat - ensure one chat per customer
        chat = None
        if chat_id:
            # Try to get the chat by ID
            try:
                chat = Chat.objects.get(id=chat_id, customer=customer)
            except Chat.DoesNotExist:
                # Chat was deleted or doesn't belong to customer, create new one
                chat = None
        
        if not chat:
            # Check if customer already has an open or in-progress chat
            existing_chat = Chat.objects.filter(
                customer=customer,
                status__in=['OPEN', 'IN_PROGRESS']
            ).first()
            
            if existing_chat:
                chat = existing_chat
            else:
                # Create new chat only if no active chat exists
                chat = Chat.objects.create(
                    customer=customer,
                    subject="Customer Support",
                    status='OPEN'
                )
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            message=message_text,
            is_from_customer=True,
            sender_name=customer_name,
            is_read=False
        )
        
        return JsonResponse({
            'success': True,
            'chat_id': chat.id,
            'message': {
                'id': message.id,
                'text': message.message,
                'sender': message.sender_name,
                'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_from_customer': message.is_from_customer
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# --- Banner Management Views ---

@login_required(login_url='adminpanel:admin_login')
def banner_list(request):
    """
    Display list of all banners from static folder with ability to view and delete.
    """
    import os
    from django.conf import settings
    
    # Get static banners from the folder
    class BannerFile:
        def __init__(self, filename, index):
            self.filename = filename
            self.title = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.gif', '').replace('.webp', '')
            self.image_url = f'/static/images/Banner/{filename}'
            self.order = index
    
    banners = []
    banner_folder = os.path.join(settings.BASE_DIR, 'storefront', 'static', 'images', 'Banner')
    
    if os.path.exists(banner_folder):
        banner_files = sorted([f for f in os.listdir(banner_folder) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')) 
                              and not f.startswith('.')])
        
        for idx, banner_file in enumerate(banner_files):
            banner = BannerFile(banner_file, idx)
            banners.append(banner)
    
    context = {
        'page_title': 'Banner Management',
        'banners': banners,
    }
    
    return render(request, 'adminpanel/banner_list.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_http_methods(["GET", "POST"])
def banner_upload(request):
    """
    Upload a new banner image directly to static folder.
    """
    from django.contrib import messages
    import os
    from django.conf import settings
    
    if request.method == 'POST':
        image = request.FILES.get('image')
        
        if not image:
            messages.error(request, 'Banner image is required.')
            return redirect('adminpanel:banner_upload')
        
        try:
            # Save to static folder
            banner_folder = os.path.join(settings.BASE_DIR, 'storefront', 'static', 'images', 'Banner')
            os.makedirs(banner_folder, exist_ok=True)
            
            file_path = os.path.join(banner_folder, image.name)
            
            # Check if file already exists
            if os.path.exists(file_path):
                messages.warning(request, f'Banner "{image.name}" already exists. Overwriting...')
            
            with open(file_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            messages.success(request, f'Banner "{image.name}" uploaded successfully!')
            return redirect('adminpanel:banner_list')
        except Exception as e:
            messages.error(request, f'Error uploading banner: {str(e)}')
            return redirect('adminpanel:banner_upload')
    
    context = {
        'page_title': 'Upload Banner',
    }
    
    return render(request, 'adminpanel/banner_upload.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def banner_delete(request, banner_id):
    """
    Delete a banner file from static folder.
    banner_id is the filename (URL encoded)
    """
    from django.contrib import messages
    import os
    from django.conf import settings
    from urllib.parse import unquote
    
    try:
        # Decode filename from URL
        filename = unquote(banner_id)
        
        # Security check - ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            messages.error(request, 'Invalid filename')
            return redirect('adminpanel:banner_list')
        
        banner_folder = os.path.join(settings.BASE_DIR, 'storefront', 'static', 'images', 'Banner')
        file_path = os.path.join(banner_folder, filename)
        
        if os.path.isfile(file_path):
            os.remove(file_path)
            messages.success(request, f'Banner "{filename}" deleted successfully!')
        else:
            messages.error(request, 'Banner file not found')
    except Exception as e:
        messages.error(request, f'Error deleting banner: {str(e)}')
    
    return redirect('adminpanel:banner_list')


# --- Reviews Management ---

@login_required(login_url='adminpanel:admin_login')
def review_list(request):
    """
    Display all product reviews with filtering and search.
    """
    from storefront.models import ProductReview
    from django.db.models import Q, Count
    
    reviews = ProductReview.objects.select_related('product', 'user').prefetch_related('images', 'reports').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        reviews = reviews.filter(
            Q(product__name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(comment__icontains=search_query)
        )
    
    # Filter by rating
    rating_filter = request.GET.get('rating', '')
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)
    
    # Filter by product
    product_filter = request.GET.get('product', '')
    if product_filter:
        reviews = reviews.filter(product_id=product_filter)
    
    # Filter by reported
    reported_filter = request.GET.get('reported', '')
    if reported_filter == 'yes':
        reviews = reviews.annotate(report_count=Count('reports')).filter(report_count__gt=0)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sort_fields = ['created_at', '-created_at', 'rating', '-rating', 'product__name', '-product__name']
    if sort_by in valid_sort_fields:
        reviews = reviews.order_by(sort_by)
    else:
        reviews = reviews.order_by('-created_at')
    
    # Annotate with report count
    reviews = reviews.annotate(report_count=Count('reports'))
    
    # Get products for filter
    products = Product.objects.all().order_by('name')
    
    context = {
        'page_title': 'Reviews Management',
        'reviews': reviews,
        'search_query': search_query,
        'rating_filter': rating_filter,
        'product_filter': product_filter,
        'reported_filter': reported_filter,
        'sort_by': sort_by,
        'products': products,
    }
    
    return render(request, 'adminpanel/review_list.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def review_delete(request, pk):
    """
    Delete a review.
    """
    from storefront.models import ProductReview
    from django.contrib import messages
    
    review = get_object_or_404(ProductReview, pk=pk)
    product_name = review.product.name
    review.delete()
    
    messages.success(request, f'Review for "{product_name}" deleted successfully!')
    return redirect('adminpanel:review_list')


# --- Returns & Refunds Management ---

@login_required(login_url='adminpanel:admin_login')
def return_list(request):
    """
    Display all return requests with filtering.
    """
    from storefront.models import ReturnRequest
    from django.db.models import Q
    
    returns = ReturnRequest.objects.select_related('order', 'user').prefetch_related('items__order_item__product').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        returns = returns.filter(
            Q(order__id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sort_fields = ['created_at', '-created_at', 'status', '-status']
    if sort_by in valid_sort_fields:
        returns = returns.order_by(sort_by)
    else:
        returns = returns.order_by('-created_at')
    
    context = {
        'page_title': 'Returns & Refunds',
        'returns': returns,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'adminpanel/return_list.html', context)


@login_required(login_url='adminpanel:admin_login')
def return_detail(request, pk):
    """
    View details of a return request.
    """
    from storefront.models import ReturnRequest
    
    return_request = get_object_or_404(
        ReturnRequest.objects.select_related('order', 'user').prefetch_related('items__order_item__product'),
        pk=pk
    )
    
    context = {
        'page_title': f'Return Request #{return_request.id}',
        'return_request': return_request,
    }
    
    return render(request, 'adminpanel/return_detail.html', context)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def return_approve(request, pk):
    """
    Approve a return request.
    """
    from storefront.models import ReturnRequest
    from django.contrib import messages
    
    return_request = get_object_or_404(ReturnRequest, pk=pk)
    
    if return_request.status != 'pending':
        messages.warning(request, 'Only pending return requests can be approved.')
        return redirect('adminpanel:return_detail', pk=pk)
    
    return_request.status = 'approved'
    return_request.save()
    
    messages.success(request, f'Return request #{return_request.id} approved successfully!')
    return redirect('adminpanel:return_detail', pk=pk)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def return_reject(request, pk):
    """
    Reject a return request.
    """
    from storefront.models import ReturnRequest
    from django.contrib import messages
    
    return_request = get_object_or_404(ReturnRequest, pk=pk)
    
    if return_request.status != 'pending':
        messages.warning(request, 'Only pending return requests can be rejected.')
        return redirect('adminpanel:return_detail', pk=pk)
    
    return_request.status = 'rejected'
    return_request.save()
    
    messages.success(request, f'Return request #{return_request.id} rejected.')
    return redirect('adminpanel:return_detail', pk=pk)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def return_process(request, pk):
    """
    Process (complete) a return request and update order status.
    This will:
    1. Mark return as processed
    2. Update order status to CANCELLED
    3. Restore product stock
    """
    from storefront.models import ReturnRequest
    from django.contrib import messages
    
    return_request = get_object_or_404(ReturnRequest, pk=pk)
    
    if return_request.status != 'approved':
        messages.warning(request, 'Only approved return requests can be processed.')
        return redirect('adminpanel:return_detail', pk=pk)
    
    try:
        # Mark return as processed
        return_request.status = 'processed'
        return_request.save()
        
        # Update order status
        order = return_request.order
        order.fulfillment_status = 'CANCELLED'
        order.save()
        
        # Restore stock for returned items
        for return_item in return_request.items.all():
            order_item = return_item.order_item
            product = order_item.product
            if product:
                product.quantity_on_hand += return_item.quantity
                product.save()
        
        messages.success(request, f'Return request #{return_request.id} processed successfully! Order cancelled and stock restored.')
    except Exception as e:
        messages.error(request, f'Error processing return: {str(e)}')
    
    return redirect('adminpanel:return_detail', pk=pk)


@login_required(login_url='adminpanel:admin_login')
@require_POST
def return_delete(request, pk):
    """
    Delete a return request.
    """
    from storefront.models import ReturnRequest
    from django.contrib import messages
    
    return_request = get_object_or_404(ReturnRequest, pk=pk)
    return_id = return_request.id
    
    # Delete associated images
    for item in return_request.items.all():
        if item.image:
            item.image.delete()
    
    # Delete the return request (cascade will delete items)
    return_request.delete()
    
    messages.success(request, f'Return request #{return_id} deleted successfully!')
    return redirect('adminpanel:return_list')
