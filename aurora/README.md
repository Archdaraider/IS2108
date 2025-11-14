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
# not sure about this
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

# might not be needed?
### Step 8: Populate categories and subcategories

```bash
python manage.py populate_categories
```

This command creates Category and SubCategory entries from existing products in the database.

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

### Creating Migrations
After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```
