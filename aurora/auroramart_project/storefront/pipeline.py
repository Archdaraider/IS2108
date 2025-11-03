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
        
        if not customer:
            # Extract name from details
            name = details.get('fullname', '') or f"{details.get('first_name', '')} {details.get('last_name', '')}".strip()
            if not name:
                name = user.username or user.email.split('@')[0]
            
            # Create customer with minimal required fields (user will complete profile in onboarding)
            Customer.objects.create(
                user=user,
                email=user.email,
                name=name,
                age=25,  # Default age - user should update this in onboarding
                gender='Male',  # Default - user should update this
                employment_status='Full-time',  # Default
                occupation='Not specified',  # Default
                education='Bachelor',  # Default
                household_size=1,  # Default
                has_children=False,  # Default
                monthly_income_sgd=5000.00,  # Default
                preferred_category='Electronics',  # Default
            )
    
    # Return dict to continue pipeline
    return {
        'is_new': is_new
    }

