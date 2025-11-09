"""
Management command to import customers from b2c_customers_100.csv
"""
import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from adminpanel.models import Customer


class Command(BaseCommand):
    help = 'Import customers from b2c_customers_100.csv'

    def handle(self, *args, **options):
        # Get the path to the CSV file
        # BASE_DIR is the project directory, need to go up to workspace root
        base_path = settings.BASE_DIR
        # Navigate to workspace root where data folder is
        while base_path.name != 'IS2108' and len(base_path.parts) > 1:
            base_path = base_path.parent
        csv_path = os.path.join(base_path, 'data', 'b2c_customers_100.csv')
        
        # Alternative: if the above doesn't work, try relative to BASE_DIR
        if not os.path.exists(csv_path):
            csv_path = os.path.join(settings.BASE_DIR.parent.parent.parent, 'data', 'b2c_customers_100.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_path}'))
            return
        
        self.stdout.write(f'Reading customers from {csv_path}...')
        
        customers_created = 0
        customers_updated = 0
        errors = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for idx, row in enumerate(reader, start=1):
                    try:
                        # Generate email if not present
                        email = f"customer{idx:03d}@auroramart.com"
                        
                        # Map CSV columns to model fields
                        age = int(row['age'].strip())
                        gender = row['gender'].strip()
                        employment_status = row['employment_status'].strip()
                        occupation = row['occupation'].strip()
                        education = row['education'].strip()
                        household_size = int(row['household_size'].strip())
                        has_children = row['has_children'].strip().lower() in ['1', 'true', 'yes']
                        monthly_income_sgd = float(row['monthly_income_sgd'].strip())
                        preferred_category = row['preferred_category'].strip()
                        
                        # Generate a name based on gender and index
                        name = f"Customer {idx:03d}"
                        
                        # Check if customer already exists
                        customer = Customer.objects.filter(email=email).first()
                        
                        if customer:
                            # Update existing customer
                            customer.age = age
                            customer.gender = gender
                            customer.employment_status = employment_status
                            customer.occupation = occupation
                            customer.education = education
                            customer.household_size = household_size
                            customer.has_children = has_children
                            customer.monthly_income_sgd = monthly_income_sgd
                            customer.preferred_category = preferred_category
                            customer.name = name
                            customer.save()
                            customers_updated += 1
                        else:
                            # Create new customer
                            # Also create a User account for authentication
                            username = f"customer{idx:03d}"
                            # Check if username exists, if so, use a different one
                            base_username = username
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}{counter}"
                                counter += 1
                            
                            # Create User account with a default password
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password='changeme123',  # Default password - users should change this
                                first_name=name.split()[0] if len(name.split()) > 0 else name,
                            )
                            
                            # Create Customer profile
                            customer = Customer.objects.create(
                                user=user,
                                email=email,
                                name=name,
                                age=age,
                                gender=gender,
                                employment_status=employment_status,
                                occupation=occupation,
                                education=education,
                                household_size=household_size,
                                has_children=has_children,
                                monthly_income_sgd=monthly_income_sgd,
                                preferred_category=preferred_category,
                            )
                            customers_created += 1
                            
                    except Exception as e:
                        errors.append(f"Error processing row {idx}: {str(e)}")
                        self.stdout.write(self.style.WARNING(f'Error processing customer {idx}: {str(e)}'))
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully imported customers:\n'
                        f'  Created: {customers_created}\n'
                        f'  Updated: {customers_updated}\n'
                        f'  Errors: {len(errors)}'
                    )
                )
                
                if errors:
                    self.stdout.write(self.style.ERROR('\nErrors encountered:'))
                    for error in errors[:10]:  # Show first 10 errors
                        self.stdout.write(self.style.ERROR(f'  - {error}'))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to read CSV file: {str(e)}'))

