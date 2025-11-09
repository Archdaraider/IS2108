"""
Custom template filters for subcategory icons.
"""
from django import template

register = template.Library()

# Mapping of subcategory names to Font Awesome icons
SUBCATEGORY_ICONS = {
    # Electronics
    'phones': 'fa-mobile-alt',
    'laptops': 'fa-laptop',
    'tablets': 'fa-tablet-alt',
    'headphones': 'fa-headphones',
    'cameras': 'fa-camera',
    'gaming': 'fa-gamepad',
    'audio': 'fa-music',
    'tv': 'fa-tv',
    'smartwatch': 'fa-clock',
    
    # Fashion
    'shirts': 'fa-tshirt',
    'pants': 'fa-user',
    'shoes': 'fa-shoe-prints',
    'dresses': 'fa-tshirt',
    'accessories': 'fa-gem',
    'bags': 'fa-shopping-bag',
    'jewelry': 'fa-ring',
    'watches': 'fa-clock',
    'sunglasses': 'fa-sun',
    
    # Beauty & Personal Care
    'skincare': 'fa-spa',
    'makeup': 'fa-palette',
    'haircare': 'fa-cut',
    'fragrance': 'fa-spray-can',
    'bath': 'fa-bath',
    'tools': 'fa-tools',
    
    # Home & Kitchen
    'furniture': 'fa-couch',
    'decor': 'fa-home',
    'kitchen': 'fa-utensils',
    'bedding': 'fa-bed',
    'lighting': 'fa-lightbulb',
    'storage': 'fa-box',
    'appliances': 'fa-blender',
    
    # Sports & Outdoors
    'fitness': 'fa-dumbbell',
    'running': 'fa-running',
    'cycling': 'fa-bicycle',
    'swimming': 'fa-swimmer',
    'camping': 'fa-campground',
    'hiking': 'fa-mountain',
    'yoga': 'fa-om',
    
    # Books
    'fiction': 'fa-book',
    'non-fiction': 'fa-book-open',
    'comics': 'fa-book-reader',
    'manga': 'fa-book',
    'children': 'fa-child',
    'textbooks': 'fa-graduation-cap',
    
    # Groceries & Gourmet
    'beverages': 'fa-wine-bottle',
    'snacks': 'fa-cookie',
    'organic': 'fa-leaf',
    'frozen': 'fa-snowflake',
    'dairy': 'fa-cheese',
    'meat': 'fa-drumstick-bite',
    
    # Automotive
    'parts': 'fa-cog',
    'accessories': 'fa-car',
    'tools': 'fa-wrench',
    'tires': 'fa-circle',
    'electronics': 'fa-plug',
    
    # Health
    'vitamins': 'fa-pills',
    'supplements': 'fa-capsules',
    'medical': 'fa-heartbeat',
    'wellness': 'fa-spa',
    
    # Pet Supplies
    'dogs': 'fa-dog',
    'cats': 'fa-cat',
    'fish': 'fa-fish',
    'birds': 'fa-dove',
    'food': 'fa-bowl-food',
    'toys': 'fa-baseball',
    
    # Default fallback
    'default': 'fa-tag',
}

@register.filter
def subcategory_icon(subcategory_name):
    """
    Returns the appropriate Font Awesome icon class for a subcategory.
    """
    if not subcategory_name:
        return 'fa-tag'
    
    # Normalize the subcategory name (lowercase, remove spaces, handle special chars)
    normalized = subcategory_name.lower().strip()
    
    # Try exact match first
    if normalized in SUBCATEGORY_ICONS:
        return SUBCATEGORY_ICONS[normalized]
    
    # Try partial matches for common patterns
    for key, icon in SUBCATEGORY_ICONS.items():
        if key in normalized or normalized in key:
            return icon
    
    # Try matching common words
    if 'phone' in normalized or 'mobile' in normalized:
        return 'fa-mobile-alt'
    elif 'laptop' in normalized or 'computer' in normalized:
        return 'fa-laptop'
    elif 'shoe' in normalized or 'footwear' in normalized:
        return 'fa-shoe-prints'
    elif 'shirt' in normalized or 'top' in normalized:
        return 'fa-tshirt'
    elif 'pant' in normalized or 'trouser' in normalized:
        return 'fa-user'
    elif 'book' in normalized or 'novel' in normalized:
        return 'fa-book'
    elif 'food' in normalized or 'grocery' in normalized:
        return 'fa-utensils'
    elif 'beauty' in normalized or 'makeup' in normalized:
        return 'fa-palette'
    elif 'sport' in normalized or 'fitness' in normalized:
        return 'fa-dumbbell'
    elif 'home' in normalized or 'furniture' in normalized:
        return 'fa-home'
    elif 'electronic' in normalized or 'tech' in normalized:
        return 'fa-microchip'
    elif 'car' in normalized or 'auto' in normalized or 'vehicle' in normalized:
        return 'fa-car'
    elif 'pet' in normalized or 'animal' in normalized:
        return 'fa-paw'
    elif 'health' in normalized or 'medical' in normalized:
        return 'fa-heartbeat'
    
    # Default fallback
    return SUBCATEGORY_ICONS.get('default', 'fa-tag')

