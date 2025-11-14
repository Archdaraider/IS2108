# IS2108 - AuroraMart E-Commerce Platform

IS2108 Pair Project - A Django-based e-commerce platform with machine learning recommendations.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Setup Instructions

### Step 1: Navigate to the aurora folder

```bash
cd aurora
```

### Step 2: Create virtual environment

```bash
python -m venv venv
```

### Step 3: Activate virtual environment

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Python packages

```bash
pip install -r requirements.txt
```

### Step 5: Navigate to project directory

```bash
cd auroramart_project
```

### Step 6: Run database migrations

```bash
python manage.py migrate
```

### Step 7: Create admin user (optional but recommended)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account. You can also use the setup command:

```bash
python manage.py setup_admin
```

This will create a default admin user:
- Username: `admin`
- Password: `admin123`

### Step 8: Populate categories and subcategories

```bash
python manage.py populate_categories
```

This command creates Category and SubCategory entries from existing products in the database.

### Step 9: Import product reviews (optional but recommended)

To populate products with reviews and ratings from the dataset:

```bash
python manage.py import_reviews
```

**Options:**
- `--clear`: Clear existing reviews before importing
- `--reviews-per-product N`: Number of reviews to generate per product (default: 10)

**Example:**
```bash
python manage.py import_reviews --reviews-per-product 15
```

This will:
- Generate reviews based on product ratings from `data/b2c_products_500.csv`
- Create review users automatically
- Display reviews on product detail pages
- Update product card ratings to reflect review averages

### Step 10: Run the development server

```bash
python manage.py runserver
```

## Accessing the Application

### Storefront (Customer-facing)
- **URL:** http://127.0.0.1:8000/
- Browse products, add to cart, place orders, view reviews

### Admin Panel
- **URL:** http://127.0.0.1:8000/admin
- Manage products, orders, customers, reviews, and returns

## Project Structure

```
aurora/
├── data/                          # Dataset files (CSV)
│   ├── b2c_products_500.csv
│   ├── b2c_customers_100.csv
│   └── b2c_products_500_transactions_50k.csv
├── auroramart_project/            # Django project
│   ├── adminpanel/                # Admin panel app
│   ├── storefront/                # Storefront app
│   ├── manage.py
│   └── ...
├── models/                        # ML model notebooks
│   ├── association_rules_mining.ipynb
│   └── decision_tree_classifier.ipynb
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Key Features

- **Product Catalog:** Browse products by category and subcategory
- **Shopping Cart:** Add products to cart and checkout
- **User Authentication:** Registration, login, and profile management
- **Order Management:** View order history and track orders
- **Product Reviews:** View and submit product reviews with ratings
- **Wishlist:** Save favorite products
- **Return/Refund System:** Request returns and refunds
- **ML Recommendations:** 
  - Personalized recommendations based on user profile
  - Frequently bought together suggestions
  - Complete the set recommendations
  - Next best action recommendations

## Important Notes

1. **Data Folder:** The `data/` folder must be in the `aurora/` directory for management commands to work properly.

2. **Database:** The project uses SQLite by default. The database file is `auroramart_project/db.sqlite3`.

3. **Media Files:** Product images and user uploads are stored in `auroramart_project/media/`.

4. **ML Models:** Pre-trained models are located in `adminpanel/mlmodels/`:
   - `b2c_customers_100.joblib` - Decision Tree for customer classification
   - `b2c_products_500_transactions_50k.joblib` - Association Rules for product recommendations

## Troubleshooting

### CSV file not found error
If you get an error about CSV files not being found:
- Ensure the `data/` folder is in the `aurora/` directory
- Check that `b2c_products_500.csv` exists in `aurora/data/`

### Migration errors
If you encounter migration errors:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static files not loading
Collect static files:
```bash
python manage.py collectstatic --noinput
```

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Support

For issues or questions, please refer to the project documentation or contact the development team.
