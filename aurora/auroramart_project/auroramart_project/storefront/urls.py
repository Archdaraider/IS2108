from django.urls import path
from . import views

urlpatterns = [
    # Main storefront pages
    path('', views.homepage, name='homepage'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.shopping_cart, name='shopping_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    
    # Category pages
    path('category/<slug:category_slug>/', views.product_list, name='category_products'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.product_list, name='subcategory_products'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # AJAX endpoints
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('api/subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
]