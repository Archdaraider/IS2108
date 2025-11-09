# adminpanel/urls.py
from django.urls import path
from . import views
from .views import AdminLoginView, AdminLogoutView

urlpatterns = [
    # Authentication
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', AdminLogoutView.as_view(), name='admin_logout'),
    path('customer-home/', views.customer_landing_page, name='customer_landing_page'),

    # Main page
    path('', views.admin_dashboard_home, name='admin_dashboard_home'),
    path('customers/', views.customer_list, name='customer_list'),
    path('products/', views.product_list, name='product_list'),
    path('orders/', views.order_list, name='order_list'),
    
    # Product Detail and Delete
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    
    # Catalogue Management
    path('catalogue/', views.catalogue_view, name='catalogue_view'),
    path('catalogue/<int:pk>/toggle/', views.catalogue_toggle_active, name='catalogue_toggle_active'),
    path('catalogue/bulk-update/', views.catalogue_bulk_update, name='catalogue_bulk_update'),
    
    # Admin User Management (Superuser only)
    path('admin-users/', views.admin_users_list, name='admin_users_list'),
    path('admin-users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),
    
    #path('reports/', views.custom_reports, name='custom_reports'),
    path('ai-studio/', views.ai_studio_home, name='ai_studio_home'),
]
