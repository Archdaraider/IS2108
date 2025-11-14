"""
Management command to list all products that have association rules.
Usage: python manage.py list_products_with_rules
"""
from django.core.management.base import BaseCommand
from storefront.recommendations import load_association_rules
from adminpanel.models import Product


class Command(BaseCommand):
    help = 'List all products that have association rules (can be used for recommendations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['list', 'csv', 'summary'],
            default='summary',
            help='Output format: list (full list), csv (CSV format), summary (summary only)',
        )
        parser.add_argument(
            '--check-db',
            action='store_true',
            help='Also check which products exist in the database',
        )

    def handle(self, *args, **options):
        rules = load_association_rules()
        
        if rules.empty:
            self.stdout.write(
                self.style.ERROR('No association rules found. Model file may be missing.')
            )
            return
        
        # Get all products from rules
        all_products = set()
        antecedent_products = set()
        consequent_products = set()
        
        # Extract products from antecedents
        for antecedents in rules['antecedents']:
            if hasattr(antecedents, '__iter__') and not isinstance(antecedents, str):
                antecedent_products.update(antecedents)
                all_products.update(antecedents)
            else:
                antecedent_products.add(antecedents)
                all_products.add(antecedents)
        
        # Extract products from consequents
        for consequents in rules['consequents']:
            if hasattr(consequents, '__iter__') and not isinstance(consequents, str):
                consequent_products.update(consequents)
                all_products.update(consequents)
            else:
                consequent_products.add(consequents)
                all_products.add(consequents)
        
        # Sort products
        all_products = sorted(list(all_products))
        antecedent_products = sorted(list(antecedent_products))
        consequent_products = sorted(list(consequent_products))
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('ASSOCIATION RULES SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f'\nTotal number of association rules: {len(rules)}')
        self.stdout.write(f'Total unique products in rules: {len(all_products)}')
        self.stdout.write(f'Products that can be used as INPUT (antecedents): {len(antecedent_products)}')
        self.stdout.write(f'Products that can be RECOMMENDED (consequents): {len(consequent_products)}')
        
        # Check database if requested
        if options['check_db']:
            self.stdout.write('\n' + '-'*80)
            self.stdout.write('DATABASE CHECK')
            self.stdout.write('-'*80)
            
            products_in_db = Product.objects.filter(sku__in=all_products).values_list('sku', flat=True)
            products_in_db_set = set(products_in_db)
            products_not_in_db = set(all_products) - products_in_db_set
            
            self.stdout.write(f'\nProducts with rules that exist in database: {len(products_in_db_set)}')
            self.stdout.write(f'Products with rules NOT in database: {len(products_not_in_db)}')
            
            if products_not_in_db:
                self.stdout.write(self.style.WARNING('\nProducts with rules but NOT in database:'))
                for sku in sorted(products_not_in_db)[:20]:  # Show first 20
                    self.stdout.write(f'  - {sku}')
                if len(products_not_in_db) > 20:
                    self.stdout.write(f'  ... and {len(products_not_in_db) - 20} more')
        
        # Output format
        format_type = options['format']
        
        if format_type == 'summary':
            # Show first 20 products as examples
            self.stdout.write('\n' + '='*80)
            self.stdout.write('FIRST 20 PRODUCTS WITH ASSOCIATION RULES:')
            self.stdout.write('='*80)
            for i, product in enumerate(all_products[:20], 1):
                in_antecedents = '✓' if product in antecedent_products else ' '
                in_consequents = '✓' if product in consequent_products else ' '
                self.stdout.write(f'{i:3d}. [{in_antecedents} Input] [{in_consequents} Recommended] {product}')
            
            if len(all_products) > 20:
                self.stdout.write(f'\n... and {len(all_products) - 20} more products')
                self.stdout.write('\nUse --format=list to see all products')
        
        elif format_type == 'list':
            self.stdout.write('\n' + '='*80)
            self.stdout.write('ALL PRODUCTS WITH ASSOCIATION RULES:')
            self.stdout.write('='*80)
            for i, product in enumerate(all_products, 1):
                in_antecedents = '✓' if product in antecedent_products else ' '
                in_consequents = '✓' if product in consequent_products else ' '
                self.stdout.write(f'{i:4d}. [{in_antecedents} Input] [{in_consequents} Recommended] {product}')
        
        elif format_type == 'csv':
            self.stdout.write('\n' + '='*80)
            self.stdout.write('PRODUCTS WITH ASSOCIATION RULES (CSV):')
            self.stdout.write('='*80)
            self.stdout.write('SKU,Can_Be_Input,Can_Be_Recommended')
            for product in all_products:
                can_input = 'Yes' if product in antecedent_products else 'No'
                can_recommend = 'Yes' if product in consequent_products else 'No'
                self.stdout.write(f'{product},{can_input},{can_recommend}')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('Done!'))

