import joblib
import os
import pandas as pd
from decimal import Decimal
from django.db.models import Count, Sum, F, DecimalField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .models import Customer, Product, Order, OrderItem, DecisionTreeModel
from django.db import models
from .forms import CustomerForm, ProductForm, OrderForm, OrderItemFormSet # Ensure OrderItemFormSet is imported
from django.http import HttpResponseNotAllowed
from django.apps import apps
from django.db import transaction # Keep transaction import
from django.forms import inlineformset_factory
from django.http import HttpResponse
from django.contrib.auth import logout

# --- Load Models Once ---
app_path = apps.get_app_config('adminpanel').path

# Load the CUSTOMER classification model
model_path = os.path.join(app_path, 'mlmodels', 'b2c_customers_100.joblib')
try:
    customer_model = joblib.load(model_path)
except FileNotFoundError:
    customer_model = None
    print("WARNING: Customer model file not found.")

# Load the PRODUCT association rules
rules_path = os.path.join(app_path, 'mlmodels', 'b2c_products_500_transactions_50k.joblib')
try:
    product_rules = joblib.load(rules_path)
except FileNotFoundError:
    product_rules = None
    print("WARNING: Product association rules file not found.")

# --- Authentication Views ---

class AdminLoginView(LoginView):
    """Custom login view for the admin panel."""
    template_name = 'adminpanel/login.html'
    next_page = 'admin_dashboard_home'

class AdminLogoutView(LogoutView):
    """
    Standard LogoutView. Renders the template AFTER logout.
    It will now automatically require a POST request for security.
    """
    template_name = 'adminpanel/logout.html' # Keep this for the confirmation page
    
def customer_landing_page(request):
    """
    A placeholder view for the customer-facing website homepage.
    """
    return HttpResponse("<h1>Customer Landing Page (Placeholder)</h1><p>This page is not built yet.</p>")
# --- Core Dashboard View ---

@login_required(login_url='admin_login')
def admin_dashboard_home(request):
    """
    Main Dashboard View - Gathers KPIs and initial data for index.html.
    """
    kpis = {
        'total_customers': Customer.objects.count(),
        'total_products': Product.objects.count(),
        'active_models': DecisionTreeModel.objects.filter(is_active=True).count(),
        'total_transactions': Order.objects.count(),
    }

    inventory_alerts = Product.objects.filter(
        quantity_on_hand__lte=models.F('reorder_quantity')
    ).order_by('quantity_on_hand')[:10]

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


# --- Product List/Create/Detail/Delete Views ---

@login_required(login_url='admin_login')
def product_list(request):
    """View to LIST and CREATE Products on one page."""
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
def product_detail(request, pk):
    """View to display and update a single product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    context = {
        'page_title': f'Edit {product.name}',
        'form': form,
        'product': product
    }
    return render(request, 'adminpanel/product_detail.html', context)

@login_required(login_url='admin_login')
def product_delete(request, pk):
    """View to delete a single product."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')


# --- Order List/Create/Detail/Delete Views ---

@login_required(login_url='admin_login')
def order_list(request):
    """View to LIST and CREATE Orders, now with OrderItems."""
    orders = Order.objects.all().order_by('-placed_at')[:100]

    # Define the formset factory here (unbound to an instance)
    OrderItemFormSetFactory = inlineformset_factory(Order, OrderItem, form=OrderItemFormSet.form, extra=1, can_delete=True)


    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSetFactory(request.POST) # Use the factory

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
                    if item.product:
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

                return redirect('order_list')
        # If form or formset is invalid, it will fall through to render the context below

    else: # GET request
        form = OrderForm()
        # Create an empty formset for a new, blank order
        formset = OrderItemFormSetFactory(queryset=OrderItem.objects.none())

    context = {
        'page_title': 'Order List',
        'orders': orders,
        'form': form,
        'formset': formset # Pass the formset to the template
    }
    return render(request, 'adminpanel/order_list.html', context)

# ---
# FIXED `order_detail` VIEW
# ---
@login_required(login_url='admin_login')
def order_detail(request, pk):
    """
    View to display and update a single order and its items.
    (Fixed NOT NULL constraint failure on unit_price during updates)
    """
    order = get_object_or_404(Order, pk=pk)

    # DEFINE THE FORMSET FACTORY HERE (OUTSIDE THE IF/ELSE BLOCK)
    OrderItemFormSetFactory = inlineformset_factory(
        Order, OrderItem, form=OrderItemFormSet.form, extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        # Use the factory to create the formset instance with POST data
        formset = OrderItemFormSetFactory(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 1. Save main order details
                    order = form.save()

                    # 2. Process deletions first (handles items marked by the DELETE checkbox)
                    # REMOVED: formset.save_clean(commit=False) - This caused the error!
                    for item_form in formset.deleted_forms:
                        if item_form.instance.pk:
                            item_form.instance.delete()

                    # 3. Process new and updated items, setting unit_price manually
                    items_to_save = formset.save(commit=False)
                    for item in items_to_save:
                        # item.product might be None if the user selected nothing in a new line, 
                        # but formset.is_valid() should handle that. We check just in case.
                        if item.product: 
                            # CRITICAL FIX: Explicitly set unit_price before saving
                            # This prevents the NOT NULL constraint failure
                            item.unit_price = item.product.price
                            item.save() 
                        # Else: If item.product is None, it means the row was empty or invalid, 
                        # which is okay if it's a new, empty extra form.

                    # 4. Recalculate the total from the database after all saves/deletes
                    total_result = order.items.aggregate(
                        total=Sum(F('unit_price') * F('quantity'), output_field=DecimalField())
                    )
                    new_total = total_result['total'] or Decimal('0.00') 

                    # 5. Save the final, correct total
                    order.total_amount = new_total
                    order.save(update_fields=['total_amount'])

                    return redirect('order_detail', pk=order.pk)

            except Exception as e:
                # Add error to the main form to be displayed
                form.add_error(None, f"An error occurred while saving: {e}")
        
        else: # Form or formset was invalid
            # Add clearer error messages if validation fails
            if not formset.is_valid():
                form.add_error(None, "Please correct the errors in the product items.")
            if not form.is_valid():
                form.add_error(None, "Please correct the errors in the order details.")
            
    else: # GET request
        form = OrderForm(instance=order)
        # Use the factory to create the formset instance for the GET request
        formset = OrderItemFormSetFactory(instance=order)

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

@login_required(login_url='admin_login')
def order_delete(request, pk):
    """View to delete a single order (the entire order)."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return redirect('order_list')


# --- Customer Views (Unchanged) ---
@login_required(login_url='admin_login')
def customer_list(request):
    """
    Handles LISTING customers and CREATING new ones with AI prediction.
    """
    customers = Customer.objects.all().order_by('-id') # Get list for GET request

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():

            # --- AI MODEL LOGIC (matching your notebook) ---
            if customer_model: # Only check for the model
                try:
                    customer = form.save(commit=False)

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
                        'has_children': form.cleaned_data.get('has_children'),
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

                    # 8. Assign prediction and save
                    customer.preferred_category = predicted_category
                    customer.save()
                    return redirect('customer_list') # Success!

                except Exception as e:
                    # This will show the error on the form
                    form.add_error(None, f"Could not predict category: {e}")

            else:
                # Fallback if model isn't loaded
                print("WARNING: Customer model not loaded. Saving customer without prediction.")
                form.save()
                return redirect('customer_list')
            # --- End of AI Logic ---
        # If form is invalid, fall through to render context below

    else: # GET request
        form = CustomerForm() # An empty form

    context = {
        'page_title': 'Customers',
        'customers': customers,
        'form': form
    }
    return render(request, 'adminpanel/customer_list.html', context)

@login_required(login_url='admin_login')
def customer_detail(request, pk):
    """
    Handles UPDATING an existing customer.
    """
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list') # Redirect to list after update
    else: # GET request
        form = CustomerForm(instance=customer)

    context = {
        'page_title': f'Edit {customer.name}',
        'form': form,
        'customer': customer
    }
    return render(request, 'adminpanel/customer_detail.html', context)


@login_required(login_url='admin_login')
def customer_delete(request, pk):
    """
    Handles the POST request to delete a customer.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('customer_list')

# --- AI/ML Studio View ---

@login_required(login_url='admin_login')
def ai_studio_home(request):
    """Dedicated page for deploying and monitoring AI/ML models."""
    models = DecisionTreeModel.objects.all()
    context = {'page_title': 'AI/ML Studio', 'models': models}
    return render(request, 'adminpanel/ai_studio_home.html', context)
