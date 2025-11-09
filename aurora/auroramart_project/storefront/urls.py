from django.urls import path
from . import views

urlpatterns = [
    # Main storefront pages
    path('', views.homepage, name='homepage'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.shopping_cart, name='shopping_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('complete-the-set/', views.complete_the_set, name='complete_the_set'),
    
    # Category pages
    path('category/<slug:category_slug>/', views.product_list, name='category_products'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.product_list, name='subcategory_products'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('onboarding/', views.profile_onboarding, name='profile_onboarding'),
    path('logout/', views.logout_view, name='logout'),
    
    # AJAX endpoints
    path('api/get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('api/subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('api/review-helpful/', views.review_helpful, name='review_helpful'),
    path('api/review-not-helpful/', views.review_not_helpful, name='review_not_helpful'),
    path('api/review-report/', views.review_report, name='review_report'),
    
    # OAuth Redirect Handler (for new users)
    path('oauth-redirect/', views.oauth_redirect_handler, name='oauth_redirect_handler'),
    
    # Account Management
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/addresses/', views.account_addresses, name='account_addresses'),
    path('account/addresses/add/', views.account_address_add, name='account_address_add'),
    path('account/addresses/<int:address_id>/edit/', views.account_address_edit, name='account_address_edit'),
    path('account/addresses/<int:address_id>/delete/', views.account_address_delete, name='account_address_delete'),
    path('account/payment-methods/', views.account_payment_methods, name='account_payment_methods'),
    path('account/payment-methods/add/', views.account_payment_add, name='account_payment_add'),
    path('account/payment-methods/<int:payment_id>/edit/', views.account_payment_edit, name='account_payment_edit'),
    path('account/payment-methods/<int:payment_id>/delete/', views.account_payment_delete, name='account_payment_delete'),
    path('account/reviews/', views.account_reviews, name='account_reviews'),
    path('account/returns/', views.account_returns, name='account_returns'),
    path('account/cancellations/', views.account_cancellations, name='account_cancellations'),
]