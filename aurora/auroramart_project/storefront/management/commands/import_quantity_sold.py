import csv
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from adminpanel.models import Product


class Command(BaseCommand):
    help = 'Import quantity sold for each product from transactions CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the transactions CSV file (default: auto-detect)',
        )

    def handle(self, *args, **options):
        # Find the CSV file
        csv_path = options.get('csv_path')
        
        if not csv_path:
            base_dir = Path(settings.BASE_DIR)
            aurora_dir = base_dir.parent.parent
            
            possible_paths = [
                aurora_dir / 'data' / 'b2c_products_500_transactions_50k.csv',
                aurora_dir / 'aurora' / 'data' / 'b2c_products_500_transactions_50k.csv' if aurora_dir.name != 'aurora' else None,
                aurora_dir.parent / 'aurora' / 'data' / 'b2c_products_500_transactions_50k.csv' if aurora_dir.name == 'aurora' else None,
                base_dir.parent.parent / 'data' / 'b2c_products_500_transactions_50k.csv',
            ]
            possible_paths = [p for p in possible_paths if p is not None]
            
            csv_path = None
            for path in possible_paths:
                path_str = str(path)
                if os.path.exists(path_str):
                    csv_path = path_str
                    break
        
        if not csv_path or not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(
                    'CSV file not found. Please provide the path using --csv-path option.\n'
                    'Looking for: b2c_products_500_transactions_50k.csv'
                )
            )
            return
        
        self.stdout.write(f'Reading transactions from: {csv_path}')
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        csvfile = None
        reader = None
        
        for encoding in encodings:
            try:
                csvfile = open(csv_path, 'r', encoding=encoding)
                reader = csv.reader(csvfile)
                self.stdout.write(f'Successfully opened CSV file with encoding: {encoding}')
                break
            except (UnicodeDecodeError, UnicodeError):
                if csvfile:
                    csvfile.close()
                continue
        
        if not reader:
            self.stdout.write(self.style.ERROR('Could not read CSV file with any supported encoding.'))
            return
        
        try:
            # Read header row to get SKUs
            header = next(reader)
            skus = [sku.strip() for sku in header]
            self.stdout.write(f'Found {len(skus)} products in header')
            
            # Initialize quantity sold counter for each SKU
            quantity_sold = {sku: 0 for sku in skus}
            
            # Process each transaction (row)
            transaction_count = 0
            for row in reader:
                transaction_count += 1
                if transaction_count % 5000 == 0:
                    self.stdout.write(f'Processing transaction {transaction_count}...')
                
                # Count how many times each product appears (value = 1)
                for idx, value in enumerate(row):
                    if idx < len(skus):
                        try:
                            # Value is 1 if product was purchased in this transaction
                            if int(value.strip()) == 1:
                                sku = skus[idx]
                                quantity_sold[sku] = quantity_sold.get(sku, 0) + 1
                        except (ValueError, IndexError):
                            continue
            
            self.stdout.write(f'Processed {transaction_count} transactions')
            self.stdout.write('Calculating quantity sold per product...')
            
            # Update products in database
            updated_count = 0
            not_found_count = 0
            
            for sku, qty in quantity_sold.items():
                try:
                    product = Product.objects.get(sku=sku)
                    product.quantity_sold = qty
                    product.save(update_fields=['quantity_sold'])
                    updated_count += 1
                    if updated_count % 50 == 0:
                        self.stdout.write(f'Updated {updated_count} products...')
                except Product.DoesNotExist:
                    not_found_count += 1
                    if not_found_count <= 10:  # Only show first 10 warnings
                        self.stdout.write(
                            self.style.WARNING(f'Product with SKU {sku} not found in database')
                        )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} products with quantity sold data.\n'
                    f'{not_found_count} SKUs from CSV not found in database.'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing CSV: {str(e)}'))
            import traceback
            traceback.print_exc()
        finally:
            if csvfile:
                csvfile.close()

