# adminpanel/urls.py
from django.urls import path
from . import views
from .views import AdminLoginView

app_name = 'adminpanel'  # Add namespace to prevent URL conflicts with storefront

urlpatterns = [
    # Authentication
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
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
    path('customers/<int:pk>/toggle-active/', views.customer_toggle_active, name='customer_toggle_active'),
    
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    
    # Catalogue Management
    path('catalogue/', views.catalogue_view, name='catalogue_view'),
    path('catalogue/<int:pk>/toggle/', views.catalogue_toggle_active, name='catalogue_toggle_active'),
    path('catalogue/bulk-update/', views.catalogue_bulk_update, name='catalogue_bulk_update'),
    
    # Admin User Management (Superuser only)
    path('admin-users/', views.admin_users_list, name='admin_users_list'),
    path('admin-users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),
    
    # Chat Support
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/<int:chat_id>/send/', views.admin_send_message, name='admin_send_message'),
    path('chats/<int:chat_id>/messages/', views.admin_get_messages, name='admin_get_messages'),
    path('chats/<int:chat_id>/status/', views.admin_update_chat_status, name='admin_update_chat_status'),
    path('chats/<int:chat_id>/delete/', views.chat_delete, name='chat_delete'),
    path('chats/bulk-delete/', views.chat_bulk_delete, name='chat_bulk_delete'),
    
    # Customer Chat API endpoints (no admin login required)
    path('api/chat/check/', views.customer_check_chat, name='customer_check_chat'),
    path('api/chat/send/', views.customer_send_message, name='customer_send_message'),
    path('api/chat/<int:chat_id>/messages/', views.customer_get_messages, name='customer_get_messages'),
    
    # Banner Management
    path('banners/', views.banner_list, name='banner_list'),
    path('banners/upload/', views.banner_upload, name='banner_upload'),
    path('banners/delete/<str:banner_id>/', views.banner_delete, name='banner_delete'),
    
    #path('reports/', views.custom_reports, name='custom_reports'),
    path('ai-studio/', views.ai_studio_home, name='ai_studio_home'),
]
