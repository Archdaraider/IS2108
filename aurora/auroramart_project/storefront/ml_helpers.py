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
    Uses the corrected approach that matches the training notebook exactly.
    
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
        
        # Convert to DataFrame and one-hot encode (same as training notebook)
        # IMPORTANT: pandas get_dummies produces columns in this order:
        # 1. Numeric columns in original order: age, household_size, has_children, monthly_income_sgd
        # 2. Then one-hot encoded columns in FULL alphabetical order (not by prefix)
        customer_df = pd.DataFrame([customer_data])
        customer_encoded = pd.get_dummies(customer_df, columns=['gender', 'employment_status', 'occupation', 'education'])
        
        # Try to get feature names from model (sklearn 1.0+)
        if hasattr(model, 'feature_names_in_'):
            expected_columns = list(model.feature_names_in_)
        else:
            # CRITICAL: Use the EXACT order from adminpanel/views.py TRAINING_COLUMNS
            # This is the exact order that was used when training the model
            # The order is: numeric columns, then gender, employment, occupation, education
            expected_columns = [
                'age',
                'household_size', 
                'has_children',
                'monthly_income_sgd',
                'gender_Female',            
                'gender_Male',
                'employment_status_Full-time',
                'employment_status_Part-time',
                'employment_status_Retired',
                'employment_status_Self-employed',
                'employment_status_Student',
                'occupation_Admin',
                'occupation_Education',
                'occupation_Sales',
                'occupation_Service',
                'occupation_Skilled Trades',
                'occupation_Tech',
                'education_Bachelor',
                'education_Diploma',
                'education_Doctorate',
                'education_Master',
                'education_Secondary'
            ]
        
        # Create result DataFrame
        result_df = pd.DataFrame(index=[0])
        
        # Populate with encoded data, ensuring all expected columns exist
        # Match notebook logic exactly: use False for bool columns, 0 for numeric
        # The notebook uses: if X[col].dtype == bool: input_encoded[col] = False else: input_encoded[col] = 0
        for col in expected_columns:
            if col in customer_encoded.columns:
                val = customer_encoded[col].iloc[0]
                # Ensure numeric columns are int/float
                if col in ['age', 'household_size', 'has_children', 'monthly_income_sgd']:
                    result_df[col] = int(val) if col != 'monthly_income_sgd' else float(val)
                else:
                    # One-hot encoded columns - convert to int (0 or 1)
                    result_df[col] = int(bool(val))
            else:
                # Missing column - match notebook logic: False for bool, 0 for numeric
                # In pandas, one-hot encoded columns are typically bool dtype
                # But since we're converting to int anyway, using 0 should be fine
                # However, let's match the notebook exactly
                if col in ['age', 'household_size', 'has_children', 'monthly_income_sgd']:
                    result_df[col] = 0
                else:
                    # For one-hot columns, use False (which will be converted to 0 by int())
                    result_df[col] = False
        
        # Reorder columns to match training data exactly (same as notebook: input_encoded[X.columns])
        result_df = result_df[expected_columns]
        
        # CRITICAL: Ensure data types match training data exactly
        # Convert all columns to match the training data dtypes
        for col in result_df.columns:
            if col in ['age', 'household_size', 'has_children']:
                result_df[col] = result_df[col].astype('int64')
            elif col == 'monthly_income_sgd':
                result_df[col] = result_df[col].astype('float64')
            else:
                # One-hot encoded columns should be int64 (0 or 1)
                result_df[col] = result_df[col].astype('int64')
        
        # Make prediction
        prediction = model.predict(result_df)
        
        result = prediction[0] if len(prediction) > 0 else None
        
        return result
        
    except Exception as e:
        print(f"Error predicting category: {e}")
        import traceback
        traceback.print_exc()
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

