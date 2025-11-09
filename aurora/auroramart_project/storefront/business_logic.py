"""
All business logic for the storefront.
This module contains all the logic that was previously in JavaScript.
All decision-making and data processing happens here.
"""

from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem, Wishlist, WishlistItem, ProductReview, ReviewHelpfulVote, ReviewReport, NewsletterSubscription
from adminpanel.models import Product
from .cart_helpers import get_or_create_cart, add_product_to_cart, update_cart_item_quantity


def add_to_cart_logic(request, product_id, quantity=1):
    """
    Add product to cart.
    Returns: (success, message)
    """
    try:
        cart = get_or_create_cart(request)
        success, message, cart_item, cart_total = add_product_to_cart(cart, product_id, quantity)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return success, message
    except Exception as e:
        messages.error(request, 'Error adding item to cart')
        return False, str(e)


def update_cart_quantity_logic(request, item_id, new_quantity):
    """
    Update cart item quantity.
    Returns: (success, message, removed)
    """
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        success, removed, updated_cart_item, cart_total = update_cart_item_quantity(cart_item, new_quantity)
        
        if success:
            if removed:
                messages.success(request, 'Item removed from cart')
            else:
                messages.success(request, 'Cart updated')
        else:
            messages.error(request, 'Error updating cart item')
        
        return success, 'Cart updated', removed
    except Exception as e:
        messages.error(request, 'Error updating cart item')
        return False, str(e), False


def remove_from_cart_logic(request, item_id):
    """
    Remove item from cart.
    Returns: (success, message)
    """
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart')
        return True, 'Item removed'
    except Exception as e:
        messages.error(request, 'Error removing item from cart')
        return False, str(e)


def toggle_wishlist_logic(request, product_id):
    """
    Toggle product in wishlist (add if not present, remove if present).
    Returns: (success, message, in_wishlist)
    """
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to use wishlist')
        return False, 'Please log in', False
    
    try:
        product = get_object_or_404(Product, id=product_id)
        wishlist = Wishlist.objects.get_or_create(user=request.user)[0]
        
        wishlist_item = WishlistItem.objects.filter(
            wishlist=wishlist,
            product=product
        ).first()
        
        if wishlist_item:
            # Item exists, remove it
            wishlist_item.delete()
            messages.success(request, f'{product.name} removed from wishlist')
            return True, f'{product.name} removed from wishlist', False
        else:
            # Item doesn't exist, add it
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=product
            )
            messages.success(request, f'{product.name} added to wishlist')
            return True, f'{product.name} added to wishlist', True
    except Exception as e:
        messages.error(request, 'Error updating wishlist')
        return False, str(e), False


def remove_from_wishlist_logic(request, item_id):
    """
    Remove item from wishlist.
    Returns: (success, message)
    """
    try:
        wishlist_item = get_object_or_404(WishlistItem, id=item_id)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        messages.success(request, f'{product_name} removed from wishlist')
        return True, 'Item removed'
    except Exception as e:
        messages.error(request, 'Error removing item from wishlist')
        return False, str(e)


def mark_review_helpful_logic(request, review_id):
    """
    Mark a review as helpful or remove helpful vote.
    Returns: (success, is_helpful, helpful_count)
    """
    try:
        review = ProductReview.objects.get(id=review_id)
        vote, created = ReviewHelpfulVote.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'is_helpful': True}
        )
        
        if not created:
            # If vote exists, check if it's helpful
            if vote.is_helpful:
                # Toggle: if already helpful, remove it
                vote.delete()
                is_helpful = False
            else:
                # If it was not helpful, change to helpful
                vote.is_helpful = True
                vote.save()
                is_helpful = True
        else:
            is_helpful = True
        
        helpful_count = review.helpful_count
        
        return True, is_helpful, helpful_count
    except ProductReview.DoesNotExist:
        return False, False, 0
    except Exception as e:
        return False, False, 0


def mark_review_not_helpful_logic(request, review_id):
    """
    Mark a review as not helpful.
    Returns: (success, is_not_helpful, helpful_count, not_helpful_count)
    """
    try:
        review = ProductReview.objects.get(id=review_id)
        vote, created = ReviewHelpfulVote.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'is_helpful': False}
        )
        
        if not created:
            # If vote exists, set it to not helpful
            if vote.is_helpful:
                vote.is_helpful = False
                vote.save()
        # else: already created as not helpful
        
        helpful_count = review.helpful_count
        not_helpful_count = review.helpful_votes.filter(is_helpful=False).count()
        
        return True, True, helpful_count, not_helpful_count
    except ProductReview.DoesNotExist:
        return False, False, 0, 0
    except Exception as e:
        return False, False, 0, 0


def report_review_logic(request, review_id, reason, additional_comments=''):
    """
    Report a review for abuse.
    Returns: (success, message)
    """
    try:
        review = ProductReview.objects.get(id=review_id)
        
        # Check if user already reported this review
        if ReviewReport.objects.filter(review=review, user=request.user).exists():
            return False, 'You have already reported this review'
        
        # Create report
        ReviewReport.objects.create(
            review=review,
            user=request.user,
            reason=reason,
            additional_comments=additional_comments
        )
        
        return True, 'Thank you for your report. We will review it shortly.'
    except ProductReview.DoesNotExist:
        return False, 'Review not found'
    except Exception as e:
        return False, str(e)


def subscribe_newsletter_logic(request, email):
    """
    Subscribe to newsletter.
    Returns: (success, message)
    """
    try:
        if email:
            subscription, created = NewsletterSubscription.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            
            if created:
                return True, 'Successfully subscribed to newsletter!'
            else:
                return False, 'Email already subscribed'
        else:
            return False, 'Please provide a valid email'
    except Exception as e:
        return False, 'Error subscribing to newsletter'

