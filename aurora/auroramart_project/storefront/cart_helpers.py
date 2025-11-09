"""
Helper functions for cart operations.
All cart business logic should be here.
"""
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from adminpanel.models import Product


def get_or_create_cart(request):
    """Get or create a cart for the current session or user."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': None}
        )
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'user': None}
        )
    return cart


def add_product_to_cart(cart, product_id, quantity=1):
    """
    Add a product to cart.
    Returns: (success, message, cart_item, cart_total)
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        
        if product.quantity_on_hand <= 0:
            return False, 'Product is out of stock', None, cart.total_items
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.quantity_on_hand:
                return False, f'Only {product.quantity_on_hand} items available in stock', cart_item, cart.total_items
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return True, f'{product.name} added to cart', cart_item, cart.total_items
    
    except Exception as e:
        return False, f'Error adding item to cart: {str(e)}', None, cart.total_items


def update_cart_item_quantity(cart_item, new_quantity):
    """
    Update cart item quantity.
    Returns: (success, removed, cart_item, cart_total)
    """
    try:
        if new_quantity <= 0:
            cart = cart_item.cart
            cart_item.delete()
            return True, True, None, cart.total_items
        
        if new_quantity > cart_item.product.quantity_on_hand:
            return False, False, cart_item, cart_item.cart.total_items
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        return True, False, cart_item, cart_item.cart.total_items
    
    except Exception as e:
        return False, False, cart_item, cart_item.cart.total_items if cart_item else 0

