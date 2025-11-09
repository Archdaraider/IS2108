# storefront/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from adminpanel.models import Customer


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Customer profile when a new User is created.
    This ensures every User has a corresponding Customer record in the adminpanel.
    """
    if created:
        # Check if a Customer with this email already exists (to avoid duplicates)
        if not Customer.objects.filter(email=instance.email).exists():
            # Create a basic Customer profile with minimal required fields
            Customer.objects.create(
                user=instance,
                email=instance.email,
                name=f"{instance.first_name} {instance.last_name}".strip() or instance.username,
                # Set placeholder values for required fields
                # These will be updated when the user completes their profile
                age=18,  # Placeholder, will be updated in profile_onboarding
                gender='Male',  # Placeholder
                employment_status='Student',  # Placeholder
                occupation='Not specified',  # Placeholder
                education='High School',  # Placeholder
                household_size=1,  # Placeholder
                has_children=False,  # Placeholder
                monthly_income_sgd=0.00,  # Placeholder
                preferred_category='Electronics'  # Placeholder
            )
        else:
            # Customer with email exists, link the user to it
            try:
                customer = Customer.objects.get(email=instance.email)
                if not customer.user:
                    customer.user = instance
                    customer.save()
            except Customer.DoesNotExist:
                pass


@receiver(post_save, sender=User)
def update_customer_profile(sender, instance, created, **kwargs):
    """
    Update Customer profile when User information changes.
    """
    if not created:
        try:
            customer = Customer.objects.get(user=instance)
            # Update name if it changed
            new_name = f"{instance.first_name} {instance.last_name}".strip() or instance.username
            if customer.name != new_name:
                customer.name = new_name
                customer.save()
            # Update email if it changed
            if customer.email != instance.email:
                # Check if new email is unique
                if not Customer.objects.filter(email=instance.email).exclude(id=customer.id).exists():
                    customer.email = instance.email
                    customer.save()
        except Customer.DoesNotExist:
            # Customer doesn't exist, create one
            create_customer_profile(sender, instance, created=True, **kwargs)

