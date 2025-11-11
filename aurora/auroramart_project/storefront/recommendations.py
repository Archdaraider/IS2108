"""
Recommendation system using Association Rules Mining
"""
import os
import joblib
from django.conf import settings
from adminpanel.models import Product

# Cache for loaded rules
_rules_cache = None

def load_association_rules():
    """Load association rules from joblib file."""
    global _rules_cache
    
    if _rules_cache is not None:
        return _rules_cache
    
    # Load model from adminpanel/mlmodels/ folder as per user specification
    from django.apps import apps
    app_path = apps.get_app_config('adminpanel').path
    
    # Build paths relative to project structure
    # BASE_DIR is auroramart_project/auroramart_project/
    # So BASE_DIR.parent.parent is IS2108/ (project root)
    project_root = settings.BASE_DIR.parent.parent
    
    model_paths = [
        # Primary location: adminpanel/mlmodels/ (as specified by user)
        os.path.join(app_path, 'mlmodels', 'b2c_products_500_transactions_50k.joblib'),
        # Fallback: models/ directory (where notebooks save the files)
        os.path.join(project_root, 'models', 'b2c_products_500_transactions_50k.joblib'),
        # Additional fallback: project models directory
        os.path.join(settings.BASE_DIR, 'models', 'b2c_products_500_transactions_50k.joblib'),
    ]
    
    for path in model_paths:
        if os.path.exists(path):
            try:
                _rules_cache = joblib.load(path)
                print(f"Successfully loaded association rules from: {path}")
                return _rules_cache
            except Exception as e:
                print(f"Error loading association rules from {path}: {e}")
                continue
    
    # Return empty DataFrame structure if file not found
    print("WARNING: Association rules model file not found. Using fallback category-based recommendations.")
    print("To enable ML-based recommendations, run the association_rules_mining.ipynb notebook and save the model.")
    import pandas as pd
    return pd.DataFrame(columns=['antecedents', 'consequents', 'confidence', 'lift'])

def get_recommendations(product_skus, top_n=5):
    """
    Get product recommendations based on association rules.
    
    Args:
        product_skus: List of product SKUs or single SKU
        top_n: Number of recommendations to return
    
    Returns:
        List of Product objects
    """
    if isinstance(product_skus, str):
        product_skus = [product_skus]
    
    rules = load_association_rules()
    
    if rules.empty or len(product_skus) == 0:
        # Fallback: return products from same category
        try:
            first_product = Product.objects.filter(sku=product_skus[0]).first()
            if first_product:
                return Product.objects.filter(
                    category=first_product.category
                ).exclude(sku__in=product_skus).order_by('-rating')[:top_n]
        except:
            pass
        return Product.objects.exclude(sku__in=product_skus).order_by('-rating')[:top_n]
    
    recommendations = set()
    
    for sku in product_skus:
        # Find rules where this SKU is in antecedents
        try:
            matched_rules = rules[rules['antecedents'].apply(lambda x: sku in x if hasattr(x, '__iter__') else False)]
            if not matched_rules.empty:
                # Sort by confidence and lift
                top_rules = matched_rules.sort_values(by=['confidence', 'lift'], ascending=False).head(top_n)
                for _, row in top_rules.iterrows():
                    consequents = row['consequents']
                    if hasattr(consequents, '__iter__'):
                        recommendations.update(consequents)
                    else:
                        recommendations.add(consequents)
        except Exception as e:
            print(f"Error processing SKU {sku}: {e}")
            continue
    
    # Remove items that are already in the input list
    recommendations.difference_update(set(product_skus))
    
    # Convert SKUs to Product objects
    recommended_products = Product.objects.filter(sku__in=list(recommendations)[:top_n])
    
    # If we don't have enough recommendations, fill with similar products
    if recommended_products.count() < top_n:
        try:
            first_product = Product.objects.filter(sku=product_skus[0]).first()
            if first_product:
                similar = Product.objects.filter(
                    category=first_product.category
                ).exclude(sku__in=product_skus).exclude(id__in=recommended_products.values_list('id', flat=True)).order_by('-rating')[:top_n - recommended_products.count()]
                recommended_products = list(recommended_products) + list(similar)
        except:
            pass
    
    return recommended_products[:top_n]

def get_category_recommendations(category_name, exclude_skus=None, top_n=8):
    """
    Get recommendations for products in a category using association rules.
    
    Args:
        category_name: Name of the category
        exclude_skus: List of SKUs to exclude
        top_n: Number of recommendations
    
    Returns:
        List of Product objects
    """
    if exclude_skus is None:
        exclude_skus = []
    
    # Get popular products in this category
    category_products = Product.objects.filter(category=category_name).exclude(sku__in=exclude_skus).order_by('-rating')[:10]
    
    if category_products.exists():
        # Use top product for recommendations
        top_product = category_products.first()
        recommendations = get_recommendations([top_product.sku], top_n)
        return recommendations
    
    return category_products[:top_n]

