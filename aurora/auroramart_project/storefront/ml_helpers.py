"""
ML Model Helpers for Storefront
Handles Decision Tree Classification and category mapping
"""
import os
import joblib
import pandas as pd
from django.apps import apps
from django.conf import settings
from .models import Category


# Cache for loaded models
_customer_model_cache = None


def load_customer_model():
    """Load Decision Tree model for customer category prediction."""
    global _customer_model_cache
    
    if _customer_model_cache is not None:
        return _customer_model_cache
    
    # Load model 
    app_path = apps.get_app_config('adminpanel').path
    model_path = os.path.join(app_path, 'mlmodels', 'b2c_customers_100.joblib')
    
    # Also check models/ directory as fallback 
    from django.conf import settings
    project_root = settings.BASE_DIR.parent.parent
    
    model_paths = [
        # Primary location: adminpanel/mlmodels/ 
        model_path,
        # Fallback: models/ directory 
        os.path.join(project_root, 'models', 'b2c_customers_100.joblib'),
    ]
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                _customer_model_cache = joblib.load(model_path)
                print(f"Successfully loaded customer model from: {model_path}")
                return _customer_model_cache
            except Exception as e:
                print(f"Error loading customer model from {model_path}: {e}")
                continue
    
    print("WARNING: Customer model file not found. Decision Tree predictions will not work.")
    return None


def predict_preferred_category(age, gender, employment_status, occupation, education, 
                               household_size, has_children, monthly_income_sgd):
    """
    Predict preferred category using Decision Tree model.
    Uses the corrected approach that doesn't require access to training data.
    
    Args:
        age: Customer age
        gender: Customer gender (e.g., 'Male', 'Female')
        employment_status: Employment status (e.g., 'Full-time', 'Part-time')
        occupation: Occupation (e.g., 'Tech', 'Sales')
        education: Education level (e.g., 'Bachelor', 'Master')
        household_size: Number of people in household
        has_children: Boolean or 1/0 indicating if customer has children
        monthly_income_sgd: Monthly income in SGD
    
    Returns:
        Predicted category string or None if prediction fails
    """
    model = load_customer_model()
    if model is None:
        return None
    
    try:
        # Define the exact column structure and dtypes as per sample code
        # This avoids needing access to the training data X
        columns = {
            'age': 'int64', 
            'household_size': 'int64', 
            'has_children': 'int64', 
            'monthly_income_sgd': 'float64',
            'gender_Female': 'bool', 
            'gender_Male': 'bool', 
            'employment_status_Full-time': 'bool',
            'employment_status_Part-time': 'bool', 
            'employment_status_Retired': 'bool',
            'employment_status_Self-employed': 'bool', 
            'employment_status_Student': 'bool',
            'occupation_Admin': 'bool', 
            'occupation_Education': 'bool', 
            'occupation_Sales': 'bool',
            'occupation_Service': 'bool', 
            'occupation_Skilled Trades': 'bool', 
            'occupation_Tech': 'bool',
            'education_Bachelor': 'bool', 
            'education_Diploma': 'bool', 
            'education_Doctorate': 'bool',
            'education_Master': 'bool', 
            'education_Secondary': 'bool'
        }
        
        # Create template DataFrame with correct structure
        df = pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in columns.items()})
        
        # Create customer data dictionary
        customer_data = {
            'age': int(age),
            'household_size': int(household_size),
            'has_children': 1 if has_children else 0,
            'monthly_income_sgd': float(monthly_income_sgd),
            'gender': gender,
            'employment_status': employment_status,
            'occupation': occupation,
            'education': education
        }
        
        # Convert to DataFrame and one-hot encode
        customer_df = pd.DataFrame([customer_data])
        customer_encoded = pd.get_dummies(customer_df, columns=['gender', 'employment_status', 'occupation', 'education'])
        
        # Populate template DataFrame with encoded data
        for col in df.columns:
            if col not in customer_encoded.columns:
                # Use False for bool columns, 0 for numeric
                if df[col].dtype == bool:
                    df[col] = False
                else:
                    df[col] = 0
            else:
                df[col] = customer_encoded[col]
        
        # Make prediction
        prediction = model.predict(df)
        
        return prediction[0] if len(prediction) > 0 else None
        
    except Exception as e:
        print(f"Error predicting category: {e}")
        return None


def map_category_to_slug(predicted_category):
    """
    Map predicted category name to Category slug for redirect.
    
    Args:
        predicted_category: Category name from ML model prediction
    
    Returns:
        Category slug or None if not found
    """
    if not predicted_category:
        return None
    
    # Try to find exact match first
    try:
        category = Category.objects.get(name=predicted_category, is_active=True)
        return category.slug
    except Category.DoesNotExist:
        pass
    
    # Try fuzzy matching for common variations
    # Map ML model categories to storefront categories
    category_mapping = {
        'Fashion - Women': 'fashion-women',
        'Fashion - Men': 'fashion-men',
        'Beauty & Personal Care': 'beauty-personal-care',
        'Electronics': 'electronics',
        'Home & Kitchen': 'home-kitchen',
        'Groceries & Gourmet': 'groceries-gourmet',
        'Books': 'books',
        'Health': 'health',
        'Sports & Outdoors': 'sports-outdoors',
        'Toys & Games': 'toys-games',
        'Pet Supplies': 'pet-supplies',
        'Automotive': 'automotive',
        'Apparel': 'fashion-women',  # Default to fashion-women
    }
    
    # Check mapping
    if predicted_category in category_mapping:
        slug = category_mapping[predicted_category]
        try:
            category = Category.objects.get(slug=slug, is_active=True)
            return category.slug
        except Category.DoesNotExist:
            pass
    
    # Try to find by partial match (case-insensitive)
    try:
        category = Category.objects.filter(
            name__icontains=predicted_category.split()[0] if predicted_category else '',
            is_active=True
        ).first()
        if category:
            return category.slug
    except:
        pass
    
    # Fallback: return first active category slug
    try:
        category = Category.objects.filter(is_active=True).first()
        if category:
            return category.slug
    except:
        pass
    
    return None

