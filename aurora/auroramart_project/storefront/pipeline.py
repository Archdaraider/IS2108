"""
Custom social auth pipeline for creating Customer profiles after Google OAuth
"""
from adminpanel.models import Customer

def create_customer_profile(strategy, details, backend, user=None, is_new=False, *args, **kwargs):
    """
    Create or update Customer profile after Google OAuth authentication.
    This ensures that Google OAuth users have a Customer profile with default values.
    
    Args:
        strategy: Social auth strategy
        details: User details from social provider
        backend: Authentication backend
        user: Django User object (created or retrieved)
        is_new: Boolean indicating if this is a new user
    """
    if user:
        # Check if customer exists by user or email
        customer = None
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            try:
                customer = Customer.objects.get(email=user.email)
                # Link the customer to the user if found by email
                customer.user = user
                customer.save()
            except Customer.DoesNotExist:
                pass
        
        # Don't create Customer here - let onboarding handle it
        # This ensures all users (regular registration and OAuth) go through onboarding
        # The onboarding step will create the Customer profile with proper data
    
    # Return dict to continue pipeline
    return {
        'is_new': is_new
    }

