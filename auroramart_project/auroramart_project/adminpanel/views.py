# auroramart_project/adminpanel/views.py

from django.db.models import Count, Sum, F, DecimalField
from django.shortcuts import render, redirect, get_object_or_404 # <-- Import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Customer, Product, Order, OrderItem, DecisionTreeModel
from django.db import models
# Import all forms
from .forms import CustomerForm, ProductForm, OrderForm
from django.http import HttpResponseNotAllowed # <-- Import this

# --- Authentication Views ---
# (Your Login and Logout views remain unchanged)
class AdminLoginView(LoginView):
    """Custom login view for the admin panel."""
    template_name = 'adminpanel/login.html'
    next_page = 'admin_dashboard_home'

class AdminLogoutView(LogoutView):
    """Logs out the user and redirects to the login page."""
    next_page = 'admin_login'

# --- Core Dashboard Views ---
# (Your admin_dashboard_home view remains unchanged)
@login_required(login_url='admin_login')
def admin_dashboard_home(request):
    """
    Main Dashboard View - Gathers KPIs and initial data for index.html.
    """
    kpis = {
        'total_customers': Customer.objects.count(),
        'total_products': Product.objects.count(),
        'active_models': DecisionTreeModel.objects.filter(is_active=True).count(),
        'total_orders': Order.objects.count(),
    }
    
    inventory_alerts = Product.objects.filter(
        stock__lte=models.F('reorder_threshold')
    ).order_by('stock')[:10]

    segment_summary = Customer.objects.values('preferred_category') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:5]

    model_status = DecisionTreeModel.objects.order_by('-training_date')

    context = {
        'page_title': 'Dashboard',
        'kpis': kpis,
        'inventory_alerts': inventory_alerts,
        'segment_summary': segment_summary,
        'model_status': model_status,
    }

    return render(request, 'adminpanel/index.html', context)


# --- Combined List & Create Views ---

@login_required(login_url='admin_login')
def customer_list(request):
    """View to LIST and CREATE Customers on one page."""
    # (This view remains unchanged)
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()

    customers = Customer.objects.all().order_by('-id')
    context = {
        'page_title': 'Customer List',
        'customers': customers,
        'form': form
    }
    return render(request, 'adminpanel/customer_list.html', context)


@login_required(login_url='admin_login')
def product_list(request):
    """View to LIST and CREATE Products on one page."""
    # (This view remains unchanged)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()

    products = Product.objects.all().order_by('name')
    context = {
        'page_title': 'Product List',
        'products': products,
        'form': form
    }
    return render(request, 'adminpanel/product_list.html', context)


@login_required(login_url='admin_login')
def order_list(request):
    """View to LIST and CREATE Orders on one page."""
    # (This view remains unchanged)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm()

    orders = Order.objects.all().order_by('-placed_at')[:100]
    context = {
        'page_title': 'Order List',
        'orders': orders,
        'form': form
    }
    return render(request, 'adminpanel/order_list.html', context)

# --- NEW: PRODUCT DETAIL / UPDATE VIEW ---

@login_required(login_url='admin_login')
def product_detail(request, pk):
    """
    View to display and update a single product.
    'pk' is the product's ID (Primary Key) passed from the URL.
    """
    # Get the specific product object, or return a 404 error if not found
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        # If the form is submitted, bind the POST data and FILES to the form
        # instance=product tells the form to update this specific product
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            # Redirect back to the same detail page to see the changes
            return redirect('product_detail', pk=product.pk)
    else:
        # If it's a GET request, create the form pre-filled with the product's data
        form = ProductForm(instance=product)

    context = {
        'page_title': f'Edit {product.name}',
        'form': form,
        'product': product
    }
    return render(request, 'adminpanel/product_detail.html', context)

# --- NEW: PRODUCT DELETE VIEW ---

@login_required(login_url='admin_login')
def product_delete(request, pk):
    """
    View to delete a single product.
    Only allows POST requests to prevent accidental deletion.
    """
    # Only allow this view to be accessed via a POST request
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(Product, pk=pk)
    product.delete()
    
    # After deleting, send the user back to the main product list
    return redirect('product_list')

# --- CUSTOMER DETAIL / UPDATE VIEW ---
@login_required(login_url='admin_login')
def customer_detail(request, pk):
    """
    View to display and update a single customer.
    """
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    context = {
        'page_title': f'Edit {customer.name}',
        'form': form,
        'customer': customer
    }
    return render(request, 'adminpanel/customer_detail.html', context)

# --- CUSTOMER DELETE VIEW ---
@login_required(login_url='admin_login')
def customer_delete(request, pk):
    """
    View to delete a single customer.
    Only allows POST requests.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('customer_list')

# --- ORDER DETAIL / UPDATE VIEW ---
@login_required(login_url='admin_login')
def order_detail(request, pk):
    """
    View to display and update a single order.
    """
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)

    context = {
        'page_title': f'Edit Order {order.oID}',
        'form': form,
        'order': order
    }
    return render(request, 'adminpanel/order_detail.html', context)

# --- ORDER DELETE VIEW ---
@login_required(login_url='admin_login')
def order_delete(request, pk):
    """
    View to delete a single order.
    Only allows POST requests.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return redirect('order_list')


# --- AI/ML and Reports Skeletons (No Change) ---
# (These views remain unchanged)

@login_required(login_url='admin_login')
def ai_studio_home(request):
    """Dedicated page for deploying and monitoring AI/ML models."""
    models = DecisionTreeModel.objects.all()
    context = {'page_title': 'AI/ML Studio', 'models': models}
    return render(request, 'adminpanel/ai_studio_home.html', context)


@login_required(login_url='admin_login')
def custom_reports(request):
    """Page for viewing custom reports and analytics."""
    report_.data = {'sales_by_month': [15000, 18000, 16500]}
    context = {'page_title': 'Custom Reports', 'reports': report_data}
    return render(request, 'adminpanel/reports.html', context)
