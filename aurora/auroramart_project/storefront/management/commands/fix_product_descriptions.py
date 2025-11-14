"""
Management command to fix product descriptions by replacing '?' with '-' where appropriate.
This fixes encoding issues where dashes appear as '?' in the CSV.
"""
from django.core.management.base import BaseCommand
from adminpanel.models import Product
import re


class Command(BaseCommand):
    help = 'Fix product descriptions by replacing "?" with "-" where appropriate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            original_description = product.description
            # Replace '?' with '-' when it appears between alphanumeric characters
            # Pattern: letter/digit ? letter/digit -> letter/digit - letter/digit
            fixed_description = re.sub(r'([a-zA-Z0-9])\?([a-zA-Z0-9])', r'\1-\2', original_description)
            
            if fixed_description != original_description:
                if dry_run:
                    self.stdout.write(f'\nProduct: {product.name} (SKU: {product.sku})')
                    self.stdout.write(f'  Before: {original_description[:100]}...')
                    self.stdout.write(f'  After:  {fixed_description[:100]}...')
                else:
                    product.description = fixed_description
                    product.save(update_fields=['description'])
                    updated_count += 1
                    if updated_count % 10 == 0:
                        self.stdout.write(f'Updated {updated_count} products...')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nWould update {updated_count} products'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} product descriptions.'
                )
            )

