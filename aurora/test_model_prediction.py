"""
Test script to verify the model prediction matches the notebook
Run this from the project root: python test_model_prediction.py
"""
import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'auroramart_project'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auroramart_project.settings')
django.setup()

import pandas as pd
import joblib
from django.apps import apps

# Load the model
app_path = apps.get_app_config('adminpanel').path
model_path = os.path.join(app_path, 'mlmodels', 'b2c_customers_100.joblib')

print(f"Loading model from: {model_path}")
model = joblib.load(model_path)

# Test case from notebook
raw_input = {
    'age': 29,
    'household_size': 2,
    'has_children': 1,
    'monthly_income_sgd': 5000,
    'gender': 'Female',
    'employment_status': 'Full-time',
    'occupation': 'Sales',
    'education': 'Bachelor'
}

print(f"\nTest input: {raw_input}")

# Convert to DataFrame
input_df = pd.DataFrame([raw_input])

# One-hot encode (same as notebook)
input_encoded = pd.get_dummies(input_df, columns=['gender', 'employment_status', 'occupation', 'education'])

print(f"\nAfter get_dummies, columns: {list(input_encoded.columns)}")

# Get expected columns from model
if hasattr(model, 'feature_names_in_'):
    expected_columns = list(model.feature_names_in_)
    print(f"\nModel feature_names_in_: {expected_columns}")
else:
    print("\nWARNING: Model does not have feature_names_in_")
    expected_columns = [
        'age', 'household_size', 'has_children', 'monthly_income_sgd',
        'gender_Female', 'gender_Male', 'employment_status_Full-time',
        'employment_status_Part-time', 'employment_status_Retired',
        'employment_status_Self-employed', 'employment_status_Student',
        'occupation_Admin', 'occupation_Education', 'occupation_Sales',
        'occupation_Service', 'occupation_Skilled Trades', 'occupation_Tech',
        'education_Bachelor', 'education_Diploma', 'education_Doctorate',
        'education_Master', 'education_Secondary'
    ]

# Add missing columns (same as notebook logic)
for col in expected_columns:
    if col not in input_encoded.columns:
        if col in ['age', 'household_size', 'has_children', 'monthly_income_sgd']:
            input_encoded[col] = 0
        else:
            input_encoded[col] = False

# Reorder columns to match training data
input_encoded = input_encoded[expected_columns]

print(f"\nFinal columns: {list(input_encoded.columns)}")
print(f"\nFinal values:\n{input_encoded.to_dict('records')[0]}")

# Make prediction
prediction = model.predict(input_encoded)
print(f"\nPrediction: {prediction}")

# Get probabilities
proba = model.predict_proba(input_encoded)
proba_dict = {str(k): float(v) for k, v in zip(model.classes_, proba[0])}
print(f"\nPrediction probabilities:")
for category, prob in sorted(proba_dict.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {prob*100:.2f}%")

print(f"\nExpected: 'Beauty & Personal Care'")
print(f"Actual: '{prediction[0]}'")
if prediction[0] != 'Beauty & Personal Care':
    print(f"\n❌ MISMATCH: Model predicts '{prediction[0]}' but notebook expects 'Beauty & Personal Care'")
    print(f"This suggests the model file may be different from the notebook version.")
    print(f"Consider regenerating the model from the notebook.")
else:
    print(f"\n✅ MATCH: Prediction matches notebook!")

