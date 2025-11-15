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

### Ensure that requirements.txt contains the following packages
```
Django>=5.2.5
social-auth-app-django>=5.4.0
Pillow>=12.0.0
python-decouple>=3.8
joblib>=1.3.0
mlxtend>=0.22.0
pandas>=2.0.0
scikit-learn>=1.3.0
graphviz>=0.20.0
jupyter>=1.0.0
```

### Step 5: Generate Machine Learning Models

The application requires two pre-trained ML model files that are too large to include in the repository. You need to generate them from the Jupyter notebooks:

**Required Model Files:**
- `aurora/models/b2c_customers_100.joblib` - Decision Tree classifier for customer category prediction
- `aurora/models/b2c_products_500_transactions_50k.joblib` - Association rules model for product recommendations

**To generate the models:**

1. **Generate the Decision Tree model:**
   
   **Option A: Using Jupyter Notebook (Interactive):**
   ```bash
   cd aurora/models
   jupyter notebook decision_tree_classifier.ipynb
   ```
   Then run all cells in the notebook (Cell → Run All). The model will be saved automatically.
   
   **Option B: Using command line (Non-interactive):**
   ```bash
   cd aurora/models
   jupyter nbconvert --to notebook --execute decision_tree_classifier.ipynb
   ```
   This will create `b2c_customers_100.joblib` in the `aurora/models/` directory.

2. **Generate the Association Rules model:**
   
   **Option A: Using Jupyter Notebook (Interactive):**
   ```bash
   jupyter notebook association_rules_mining.ipynb
   ```
   Then run all cells in the notebook (Cell → Run All). The model will be saved automatically.
   
   **Option B: Using command line (Non-interactive):**
   ```bash
   jupyter nbconvert --to notebook --execute association_rules_mining.ipynb
   ```
   This will create `b2c_products_500_transactions_50k.joblib` in the `aurora/models/` directory.

3. **Copy models to the Django project:**
   
   Navigate back to the `aurora` directory first:
   ```bash
   cd ..  # Go back to aurora directory
   ```
   
   **Windows:**
   ```bash
   # Copy customer model
   copy models\b2c_customers_100.joblib auroramart_project\adminpanel\mlmodels\
   
   # Copy association rules model
   copy models\b2c_products_500_transactions_50k.joblib auroramart_project\adminpanel\mlmodels\
   ```
   
   **Mac/Linux:**
   ```bash
   # Copy customer model
   cp models/b2c_customers_100.joblib auroramart_project/adminpanel/mlmodels/
   
   # Copy association rules model
   cp models/b2c_products_500_transactions_50k.joblib auroramart_project/adminpanel/mlmodels/
   ```

**Note:** The notebooks require the CSV data files in `aurora/data/` directory. Make sure these files are present before running the notebooks.

### Step 6: Navigate to project directory

```bash
cd auroramart_project
```

### Step 7: Run the development server

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

### To Log into Admin panel
- Username: `admin`
- Password: `admin`

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
│   ├── decision_tree_classifier.ipynb
│   ├── b2c_customers_100.joblib          # Generated model (not in repo)
│   └── b2c_products_500_transactions_50k.joblib  # Generated model (not in repo)
├── auroramart_project/
│   └── adminpanel/
│       └── mlmodels/              # ML model storage (generated models go here)
│           ├── b2c_customers_100.joblib
│           └── b2c_products_500_transactions_50k.joblib
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```
