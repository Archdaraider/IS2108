"""
Management command to import products from b2c_products_500.csv
"""
import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from adminpanel.models import Product


class Command(BaseCommand):
    help = 'Import products from b2c_products_500.csv'

    def handle(self, *args, **options):
        # Get the path to the CSV file
        # BASE_DIR is the project directory, need to go up to workspace root
        base_path = settings.BASE_DIR
        # Navigate to workspace root where data folder is
        while base_path.name != 'IS2108' and len(base_path.parts) > 1:
            base_path = base_path.parent
        csv_path = os.path.join(base_path, 'data', 'b2c_products_500.csv')
        
        # Alternative: if the above doesn't work, try relative to BASE_DIR
        if not os.path.exists(csv_path):
            csv_path = os.path.join(settings.BASE_DIR.parent.parent.parent, 'data', 'b2c_products_500.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_path}'))
            return
        
        self.stdout.write(f'Reading products from {csv_path}...')
        
        products_created = 0
        products_updated = 0
        errors = []
        
        try:
            with open(csv_path, 'r', encoding='latin-1') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Map CSV columns to model fields
                        sku = row['SKU code'].strip()
                        name = row['Product name'].strip()
                        description = row['Product description'].strip()
                        category = row['Product Category'].strip()
                        subcategory = row['Product Subcategory'].strip()
                        stock = int(row['Quantity on hand'].strip())
                        reorder_threshold = int(row['Reorder Quantity'].strip())
                        price = float(row['Unit price'].strip())
                        rating = float(row['Product rating'].strip())
                        
                        # Create or update product
                        product, created = Product.objects.update_or_create(
                            sku=sku,
                            defaults={
                                'name': name,
                                'description': description,
                                'category': category,
                                'subcategory': subcategory,
                                'stock': stock,
                                'reorder_threshold': reorder_threshold,
                                'price': price,
                                'rating': rating,
                            }
                        )
                        
                        if created:
                            products_created += 1
                        else:
                            products_updated += 1
                            
                    except Exception as e:
                        errors.append(f"Error processing row {row.get('SKU code', 'unknown')}: {str(e)}")
                        self.stdout.write(self.style.WARNING(f'Error processing {row.get("SKU code", "unknown")}: {str(e)}'))
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully imported products:\n'
                        f'  Created: {products_created}\n'
                        f'  Updated: {products_updated}\n'
                        f'  Errors: {len(errors)}'
                    )
                )
                
                if errors:
                    self.stdout.write(self.style.ERROR('\nErrors encountered:'))
                    for error in errors[:10]:  # Show first 10 errors
                        self.stdout.write(self.style.ERROR(f'  - {error}'))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to read CSV file: {str(e)}'))

