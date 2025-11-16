"""
Custom social auth pipeline for creating Customer profiles after Google OAuth
"""
from adminpanel.models import Customer

def create_customer_profile(strategy, details, backend, user=None, is_new=False, *args, **kwargs):
    """
    Create or update Customer profile after Google OAuth authentication.
    This ensures that Google OAuth users have a Customer profile with default values.
    """
    if user:
        # Check if customer exists by user
        customer = None
        try:
            customer = Customer.objects.get(user=user)
            # Check if profile was completed through onboarding
            # Use profile_completed field instead of checking placeholder values
            if not customer.profile_completed:
                # Profile not completed, don't link it - let onboarding create/update it
                customer = None
        except Customer.DoesNotExist:
            # Don't try to link by email - if Customer was deleted, it should stay deleted
            # Let onboarding create a fresh Customer profile
            pass
    return {
        'is_new': is_new
    }

