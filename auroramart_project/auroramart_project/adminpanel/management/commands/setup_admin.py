"""
Management command to setup the admin superuser and remove other users.
Usage: python manage.py setup_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Setup admin superuser (admin/admin) and remove other superusers'

    def handle(self, *args, **options):
        # Remove user 'justin' if exists
        try:
            justin_user = User.objects.get(username='justin')
            justin_user.delete()
            self.stdout.write(
                self.style.SUCCESS('Successfully deleted user "justin"')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('User "justin" does not exist')
            )
        
        # Remove any other superusers except 'admin'
        other_superusers = User.objects.filter(is_superuser=True).exclude(username='admin')
        for user in other_superusers:
            self.stdout.write(
                self.style.WARNING(f'Deleting superuser: {user.username}')
            )
            user.delete()
        
        if other_superusers.exists():
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {other_superusers.count()} other superuser(s)')
            )
        
        # Create or update admin user
        admin_user, created = User.objects.get_or_create(username='admin')
        
        if created:
            admin_user.set_password('admin')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.email = 'admin@auroramart.com'
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created admin user (admin/admin)')
            )
        else:
            # Update existing admin user to ensure correct settings
            admin_user.set_password('admin')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.email = admin_user.email or 'admin@auroramart.com'
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated admin user (admin/admin)')
            )
        
        # Verify only one superuser exists
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count == 1:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Verification: Only 1 superuser exists (admin)')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Warning: {superuser_count} superuser(s) exist (expected 1)')
            )

