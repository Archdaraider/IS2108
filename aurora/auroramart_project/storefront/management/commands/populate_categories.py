"""
Management command to populate categories and subcategories from existing products.
This will create Category and SubCategory entries based on the category and subcategory
fields in the Product model.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from storefront.models import Category, SubCategory
from adminpanel.models import Product
from django.db.models import Count


class Command(BaseCommand):
    help = 'Populate categories and subcategories from existing products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Categories cleared.'))

        # Get all unique categories from products
        categories_data = Product.objects.filter(
            stock__gt=0,
            category__isnull=False
        ).exclude(
            category=''
        ).values('category').annotate(
            count=Count('id')
        ).order_by('-count')

        if not categories_data:
            self.stdout.write(self.style.WARNING('No products with categories found.'))
            return

        created_categories = 0
        created_subcategories = 0

        for cat_data in categories_data:
            category_name = cat_data['category']
            product_count = cat_data['count']

            # Create or get category
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'slug': slugify(category_name),
                    'is_active': True,
                }
            )

            if created:
                created_categories += 1
                self.stdout.write(f'Created category: {category_name} ({product_count} products)')
            else:
                self.stdout.write(f'Category already exists: {category_name} ({product_count} products)')

            # Get all unique subcategories for this category
            subcategories_data = Product.objects.filter(
                category=category_name,
                subcategory__isnull=False,
                stock__gt=0
            ).exclude(
                subcategory=''
            ).values('subcategory').annotate(
                count=Count('id')
            ).order_by('-count')

            for subcat_data in subcategories_data:
                subcategory_name = subcat_data['subcategory']
                subcat_product_count = subcat_data['count']

                # Create or get subcategory
                subcategory, subcat_created = SubCategory.objects.get_or_create(
                    category=category,
                    slug=slugify(subcategory_name),
                    defaults={
                        'name': subcategory_name,
                        'is_active': True,
                    }
                )

                if subcat_created:
                    created_subcategories += 1
                    self.stdout.write(f'  Created subcategory: {subcategory_name} ({subcat_product_count} products)')
                else:
                    self.stdout.write(f'  Subcategory already exists: {subcategory_name} ({subcat_product_count} products)')

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully populated categories!\n'
            f'Created {created_categories} new categories\n'
            f'Created {created_subcategories} new subcategories'
        ))

