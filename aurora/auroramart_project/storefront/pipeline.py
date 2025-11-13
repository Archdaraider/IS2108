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
        # Check if customer exists by user
        customer = None
        try:
            customer = Customer.objects.get(user=user)
            # Check if this is a placeholder profile (not completed through onboarding)
            is_placeholder = (
                customer.age == 18 and
                customer.gender == 'Male' and
                customer.employment_status == 'Student' and
                customer.occupation == 'Sales' and
                customer.preferred_category == 'Electronics' and
                customer.monthly_income_sgd == 0.00
            )
            # If it's a placeholder, don't link it - let onboarding create a new one
            if is_placeholder:
                customer = None
        except Customer.DoesNotExist:
            # Don't try to link by email - if Customer was deleted, it should stay deleted
            # Let onboarding create a fresh Customer profile
            pass
        
        # Don't create Customer here - let onboarding handle it
        # This ensures all users (regular registration and OAuth) go through onboarding
        # The onboarding step will create the Customer profile with proper data
    
    # Return dict to continue pipeline
    return {
        'is_new': is_new
    }

