"""
Management command to import product reviews from the dataset.
Generates reviews based on product ratings in the CSV file.
"""
import csv
import os
import random
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from adminpanel.models import Product
from storefront.models import ProductReview
from django.conf import settings
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Import product reviews from dataset based on product ratings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing reviews before importing',
        )
        parser.add_argument(
            '--reviews-per-product',
            type=int,
            default=10,
            help='Number of reviews to generate per product (default: 10)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing reviews...')
            ProductReview.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Reviews cleared.'))

        reviews_per_product = options['reviews_per_product']
        
        # Find the CSV file
        # BASE_DIR is auroramart_project/auroramart_project/ (where settings.py is)
        # settings.BASE_DIR.parent = aurora/auroramart_project/
        # settings.BASE_DIR.parent.parent = aurora/ (or IS2108/ if structure is different)
        
        # Convert Path objects to strings for os.path operations
        base_dir = Path(settings.BASE_DIR)
        aurora_root = base_dir.parent.parent
        
        # Try paths in order of likelihood
        possible_paths = [
            # Path 1: aurora/data/ (if BASE_DIR.parent.parent is aurora/)
            aurora_root / 'data' / 'b2c_products_500.csv',
            # Path 2: IS2108/aurora/data/ (if BASE_DIR.parent.parent is IS2108/)
            aurora_root.parent / 'aurora' / 'data' / 'b2c_products_500.csv',
            # Path 3: Relative from auroramart_project/ going up to aurora/data/
            base_dir.parent.parent / 'data' / 'b2c_products_500.csv',
        ]
        
        csv_path = None
        for path in possible_paths:
            path_str = str(path)
            if os.path.exists(path_str):
                csv_path = path_str
                break
        
        if not csv_path:
            self.stdout.write(self.style.ERROR(f'CSV file not found. Tried:'))
            for path in possible_paths:
                self.stdout.write(self.style.ERROR(f'  - {path}'))
            self.stdout.write(self.style.ERROR(f'\nPlease ensure the data folder is in the aurora/ directory.'))
            self.stdout.write(self.style.ERROR(f'Expected location: {aurora_root.parent / "aurora" / "data" / "b2c_products_500.csv"}'))
            return

        # Sample review comments for different ratings
        review_templates = {
            5: [
                "Excellent product! Exceeded my expectations. Highly recommend!",
                "Amazing quality and value for money. Will definitely buy again.",
                "Perfect! Exactly as described. Fast shipping too.",
                "Outstanding product. Very satisfied with my purchase.",
                "Love it! Great quality and looks exactly like the picture.",
                "Best purchase I've made. Quality is top-notch.",
                "Highly recommend! Great product at a great price.",
                "Excellent quality. Very happy with this purchase.",
                "Perfect product! Exceeded all my expectations.",
                "Amazing! Great value and quality. Highly satisfied.",
            ],
            4: [
                "Good product overall. Happy with my purchase.",
                "Nice quality. Would recommend to others.",
                "Pretty good value for money. Satisfied customer.",
                "Good product, meets expectations. No complaints.",
                "Solid product. Works as expected.",
                "Decent quality. Worth the price.",
                "Good purchase. Happy with the quality.",
                "Nice product. Would buy again.",
                "Satisfactory product. Good value.",
                "Good quality. Meets my needs.",
            ],
            3: [
                "Average product. Nothing special but works fine.",
                "Okay product. Could be better but acceptable.",
                "It's alright. Does the job but nothing exceptional.",
                "Average quality. Expected more for the price.",
                "Mediocre product. Works but not impressive.",
                "Decent but could be improved.",
                "Average product. Gets the job done.",
                "Okay quality. Nothing to write home about.",
                "It's fine. Not great, not terrible.",
                "Average purchase. Could be better.",
            ],
            2: [
                "Disappointed with the quality. Expected better.",
                "Not great. Quality is below expectations.",
                "Could be better. Not satisfied with the purchase.",
                "Poor quality. Would not recommend.",
                "Not worth the price. Quality is lacking.",
                "Disappointing product. Expected more.",
                "Below average quality. Not happy with purchase.",
                "Not as described. Quality is poor.",
                "Would not buy again. Quality issues.",
                "Not satisfied. Product doesn't meet expectations.",
            ],
            1: [
                "Very poor quality. Do not recommend.",
                "Terrible product. Waste of money.",
                "Extremely disappointed. Quality is very poor.",
                "Worst purchase. Product is defective.",
                "Very bad quality. Would not recommend to anyone.",
                "Poor product. Not worth buying.",
                "Terrible quality. Very disappointed.",
                "Worst product I've bought. Avoid this.",
                "Very poor. Quality is unacceptable.",
                "Terrible purchase. Product doesn't work.",
            ],
        }

        # Sample review titles
        review_titles = {
            5: [
                "Excellent Product!",
                "Highly Recommend",
                "Amazing Quality",
                "Perfect Purchase",
                "Great Value",
                "Top Quality",
                "Outstanding Product",
                "Love It!",
                "Best Purchase",
                "Excellent Quality",
            ],
            4: [
                "Good Product",
                "Nice Quality",
                "Satisfied Customer",
                "Worth the Price",
                "Good Value",
                "Solid Product",
                "Happy with Purchase",
                "Meets Expectations",
                "Good Quality",
                "Would Recommend",
            ],
            3: [
                "Average Product",
                "It's Okay",
                "Nothing Special",
                "Gets the Job Done",
                "Mediocre Quality",
                "Average Purchase",
                "Could Be Better",
                "Just Okay",
                "Acceptable",
                "Average Quality",
            ],
            2: [
                "Disappointed",
                "Not Great",
                "Below Expectations",
                "Poor Quality",
                "Not Satisfied",
                "Could Be Better",
                "Not Worth It",
                "Disappointing",
                "Below Average",
                "Not Happy",
            ],
            1: [
                "Very Poor",
                "Terrible Quality",
                "Worst Purchase",
                "Do Not Buy",
                "Very Disappointed",
                "Poor Product",
                "Waste of Money",
                "Avoid This",
                "Terrible",
                "Very Bad",
            ],
        }

        # Get or create review users
        review_users = []
        for i in range(1, 51):  # Create 50 review users
            username = f'reviewer_{i:03d}'
            email = f'reviewer{i}@example.com'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Reviewer',
                    'last_name': f'{i}',
                }
            )
            if created:
                user.set_unusable_password()
                user.save()
            review_users.append(user)

        self.stdout.write(f'Created/found {len(review_users)} review users.')

        # Read CSV and generate reviews
        created_reviews = 0
        products_processed = 0

        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                sku = row.get('SKU code', '').strip()
                if not sku:
                    continue
                
                try:
                    product = Product.objects.get(sku=sku)
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Product with SKU {sku} not found. Skipping.'))
                    continue

                # Get product rating from CSV
                try:
                    product_rating = float(row.get('Product rating', 0))
                except (ValueError, TypeError):
                    product_rating = 0.0

                if product_rating == 0:
                    continue

                # Check if product already has reviews
                existing_reviews_count = ProductReview.objects.filter(product=product).count()
                if existing_reviews_count > 0:
                    self.stdout.write(f'Product {product.name} already has {existing_reviews_count} reviews. Skipping.')
                    continue

                # Generate reviews that average to the product rating
                reviews_to_create = []
                target_avg = product_rating
                
                # Generate ratings that will average to target_avg
                ratings = self._generate_ratings_for_average(target_avg, reviews_per_product)
                
                # Create reviews with random dates in the past 6 months
                base_date = datetime.now()
                for i, rating in enumerate(ratings):
                    # Random date within last 6 months
                    days_ago = random.randint(0, 180)
                    review_date = base_date - timedelta(days=days_ago)
                    
                    # Select random user (ensuring no duplicate reviews per product per user)
                    user = random.choice(review_users)
                    
                    # Check if this user already has a review for this product
                    if ProductReview.objects.filter(product=product, user=user).exists():
                        # Try another user
                        available_users = [u for u in review_users if not ProductReview.objects.filter(product=product, user=u).exists()]
                        if available_users:
                            user = random.choice(available_users)
                        else:
                            # All users have reviewed, skip
                            continue
                    
                    title = random.choice(review_titles[rating])
                    comment = random.choice(review_templates[rating])
                    
                    # Add some variation to comments
                    if random.random() < 0.3:  # 30% chance to add product name
                        comment = comment.replace("product", product.name.split()[0] if product.name else "product")
                    
                    review = ProductReview(
                        product=product,
                        user=user,
                        rating=rating,
                        title=title,
                        comment=comment,
                        is_verified_purchase=random.random() < 0.7,  # 70% verified purchases
                        is_anonymous=random.random() < 0.1,  # 10% anonymous
                    )
                    review.created_at = review_date
                    review.updated_at = review_date
                    reviews_to_create.append(review)

                # Bulk create reviews
                if reviews_to_create:
                    ProductReview.objects.bulk_create(reviews_to_create)
                    created_reviews += len(reviews_to_create)
                    products_processed += 1
                    self.stdout.write(
                        f'Created {len(reviews_to_create)} reviews for {product.name} '
                        f'(target avg: {target_avg:.1f}, actual avg: {sum(r.rating for r in reviews_to_create) / len(reviews_to_create):.1f})'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {created_reviews} reviews for {products_processed} products.'
        ))

    def _generate_ratings_for_average(self, target_avg, count):
        """
        Generate a list of ratings (1-5) that average to approximately target_avg.
        """
        ratings = []
        total_needed = target_avg * count
        
        # Start with ratings distributed around the target
        # For example, if target is 4.5, we want mostly 4s and 5s
        target_int = int(target_avg)
        remainder = target_avg - target_int
        
        # Calculate distribution
        if target_avg >= 4.5:
            # Mostly 5s, some 4s
            num_5s = int(count * (0.5 + remainder))
            num_4s = count - num_5s
            ratings = [5] * num_5s + [4] * num_4s
        elif target_avg >= 3.5:
            # Mix of 4s and 5s, some 3s
            num_5s = int(count * remainder * 2)
            num_4s = int(count * (0.6 + remainder * 0.2))
            num_3s = count - num_5s - num_4s
            ratings = [5] * num_5s + [4] * num_4s + [3] * max(0, num_3s)
        elif target_avg >= 2.5:
            # Mix of 3s and 4s, some 2s
            num_4s = int(count * remainder * 2)
            num_3s = int(count * (0.6 + remainder * 0.2))
            num_2s = count - num_4s - num_3s
            ratings = [4] * num_4s + [3] * num_3s + [2] * max(0, num_2s)
        elif target_avg >= 1.5:
            # Mix of 2s and 3s, some 1s
            num_3s = int(count * remainder * 2)
            num_2s = int(count * (0.6 + remainder * 0.2))
            num_1s = count - num_3s - num_2s
            ratings = [3] * num_3s + [2] * num_2s + [1] * max(0, num_1s)
        else:
            # Mostly 1s and 2s
            num_2s = int(count * remainder * 2)
            num_1s = count - num_2s
            ratings = [2] * num_2s + [1] * num_1s
        
        # Adjust to get closer to target average
        current_avg = sum(ratings) / len(ratings) if ratings else 0
        diff = target_avg - current_avg
        
        # Fine-tune by adjusting some ratings
        if abs(diff) > 0.1:  # If difference is significant
            adjustments = int(abs(diff) * count)
            if diff > 0:  # Need to increase average
                # Change some lower ratings to higher ones
                for i in range(min(adjustments, len(ratings))):
                    if ratings[i] < 5:
                        ratings[i] += 1
            else:  # Need to decrease average
                # Change some higher ratings to lower ones
                for i in range(min(adjustments, len(ratings))):
                    if ratings[i] > 1:
                        ratings[i] -= 1
        
        # Shuffle to randomize order
        random.shuffle(ratings)
        
        return ratings

