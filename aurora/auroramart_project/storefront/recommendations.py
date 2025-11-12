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
    
    This function handles multiple products intelligently:
    1. First, tries to find rules where multiple products appear together in antecedents (more specific)
    2. Then, falls back to individual product matching (broader recommendations)
    
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
    
    product_skus_set = set(product_skus)
    recommendations = set()
    recommendation_scores = {}  # Track confidence scores for ranking
    
    # Strategy 1: Find rules where multiple cart items appear together in antecedents
    # This is more specific and typically has higher confidence
    if len(product_skus) > 1:
        try:
            # Find rules where ALL cart items are in antecedents (exact match)
            def all_items_in_antecedents(antecedents):
                if not hasattr(antecedents, '__iter__'):
                    return False
                antecedents_set = set(antecedents) if isinstance(antecedents, (set, list, tuple)) else {antecedents}
                return product_skus_set.issubset(antecedents_set)
            
            exact_match_rules = rules[rules['antecedents'].apply(all_items_in_antecedents)]
            if not exact_match_rules.empty:
                # Sort by confidence and lift (highest first)
                top_rules = exact_match_rules.sort_values(by=['confidence', 'lift'], ascending=False).head(top_n * 2)
                for _, row in top_rules.iterrows():
                    consequents = row['consequents']
                    confidence = row.get('confidence', 0)
                    lift = row.get('lift', 0)
                    score = confidence * lift  # Combined score
                    
                    if hasattr(consequents, '__iter__'):
                        for consequent in consequents:
                            if consequent not in product_skus_set:
                                recommendations.add(consequent)
                                # Track best score for each recommendation
                                if consequent not in recommendation_scores or score > recommendation_scores[consequent]:
                                    recommendation_scores[consequent] = score
                    else:
                        if consequents not in product_skus_set:
                            recommendations.add(consequents)
                            if consequents not in recommendation_scores or score > recommendation_scores[consequents]:
                                recommendation_scores[consequents] = score
            
            # Strategy 1b: Find rules where a subset of cart items appear together
            # (e.g., if cart has [A, B, C], find rules with [A, B] or [B, C] in antecedents)
            if len(recommendations) < top_n:
                def subset_match(antecedents):
                    if not hasattr(antecedents, '__iter__'):
                        return False
                    antecedents_set = set(antecedents) if isinstance(antecedents, (set, list, tuple)) else {antecedents}
                    # Check if antecedents is a subset of cart items (rule applies to cart)
                    return antecedents_set.issubset(product_skus_set) and len(antecedents_set) > 1
                
                subset_match_rules = rules[rules['antecedents'].apply(subset_match)]
                if not subset_match_rules.empty:
                    top_rules = subset_match_rules.sort_values(by=['confidence', 'lift'], ascending=False).head(top_n * 2)
                    for _, row in top_rules.iterrows():
                        consequents = row['consequents']
                        confidence = row.get('confidence', 0)
                        lift = row.get('lift', 0)
                        score = confidence * lift
                        
                        if hasattr(consequents, '__iter__'):
                            for consequent in consequents:
                                if consequent not in product_skus_set:
                                    recommendations.add(consequent)
                                    if consequent not in recommendation_scores or score > recommendation_scores[consequent]:
                                        recommendation_scores[consequent] = score
                        else:
                            if consequents not in product_skus_set:
                                recommendations.add(consequents)
                                if consequents not in recommendation_scores or score > recommendation_scores[consequents]:
                                    recommendation_scores[consequents] = score
        except Exception as e:
            print(f"Error processing multi-item rules: {e}")
    
    # Strategy 2: Find rules for individual items (fallback - broader recommendations)
    # This is the original approach, now used as fallback
    if len(recommendations) < top_n:
        for sku in product_skus:
            try:
                # Find rules where this SKU is in antecedents
                matched_rules = rules[rules['antecedents'].apply(lambda x: sku in x if hasattr(x, '__iter__') else False)]
                if not matched_rules.empty:
                    # Sort by confidence and lift
                    top_rules = matched_rules.sort_values(by=['confidence', 'lift'], ascending=False).head(top_n)
                    for _, row in top_rules.iterrows():
                        consequents = row['consequents']
                        confidence = row.get('confidence', 0)
                        lift = row.get('lift', 0)
                        score = confidence * lift
                        
                        if hasattr(consequents, '__iter__'):
                            for consequent in consequents:
                                if consequent not in product_skus_set:
                                    recommendations.add(consequent)
                                    # Only update score if not already set (multi-item rules take priority)
                                    if consequent not in recommendation_scores:
                                        recommendation_scores[consequent] = score
                        else:
                            if consequents not in product_skus_set:
                                recommendations.add(consequents)
                                if consequents not in recommendation_scores:
                                    recommendation_scores[consequents] = score
            except Exception as e:
                print(f"Error processing SKU {sku}: {e}")
                continue
    
    # Remove items that are already in the input list
    recommendations.difference_update(product_skus_set)
    
    # Sort recommendations by score (highest first), then convert to list
    sorted_recommendations = sorted(recommendations, key=lambda x: recommendation_scores.get(x, 0), reverse=True)[:top_n]
    
    # Convert SKUs to Product objects
    recommended_products = Product.objects.filter(sku__in=sorted_recommendations)
    
    # Maintain order based on scores
    product_dict = {p.sku: p for p in recommended_products}
    ordered_products = [product_dict[sku] for sku in sorted_recommendations if sku in product_dict]
    
    # If we don't have enough recommendations, fill with similar products
    if len(ordered_products) < top_n:
        try:
            first_product = Product.objects.filter(sku=product_skus[0]).first()
            if first_product:
                similar = Product.objects.filter(
                    category=first_product.category
                ).exclude(sku__in=product_skus).exclude(id__in=[p.id for p in ordered_products]).order_by('-rating')[:top_n - len(ordered_products)]
                ordered_products = list(ordered_products) + list(similar)
        except:
            pass
    
    return ordered_products[:top_n]

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

