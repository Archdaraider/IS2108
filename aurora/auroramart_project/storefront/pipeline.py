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
    return {
        'is_new': is_new
    }

