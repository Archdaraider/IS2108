# AuroraMart Setup Guide

This guide explains how to set up and use all the features that have been implemented.

## Features Implemented

### 1. Database Integration
- ✅ Products imported from `b2c_products_500.csv`
- ✅ Customers imported from `b2c_customers_100.csv`
- ✅ Products linked to categories: Electronics, Fashion (Men & Women), Home & Kitchen, etc.

### 2. Product Listing by Category
- ✅ Category-based product pages for:
  - Electronics
  - Fashion - Men
  - Fashion - Women
  - Home & Kitchen
  - Beauty & Personal Care
  - Sports & Outdoors
  - Books
  - Groceries & Gourmet
  - And more...

### 3. Authentication
- ✅ Email-based login (can use email or username)
- ✅ Email-based signup
- ✅ Logout functionality
- ✅ Google OAuth integration (requires configuration)

### 4. Wishlist
- ✅ Add products to wishlist
- ✅ Remove products from wishlist
- ✅ View wishlist page
- ✅ Wishlist is user-specific and requires login

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Import Data from CSV Files

Navigate to the project directory:
```bash
cd aurora/auroramart_project
```

Import products:
```bash
python manage.py import_products
```

Import customers:
```bash
python manage.py import_customers
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

## Google OAuth Configuration

To enable Google OAuth login:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new OAuth 2.0 Client ID
3. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/oauth/complete/google-oauth2/` (for development)
   - `https://yourdomain.com/oauth/complete/google-oauth2/` (for production)
4. Set environment variables:
   ```bash
   export GOOGLE_OAUTH2_CLIENT_ID="your-client-id"
   export GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret"
   ```
   Or add them directly to `settings.py` (not recommended for production).

## Using the Application

### Login/Register

- **Email Login**: Go to `/login/` and enter your email (or username) and password
- **Sign Up**: Go to `/register/` to create a new account
- **Google Login**: Click "Continue with Google" (requires OAuth setup)

### Browsing Products

- **All Products**: Navigate to `/products/` or click "All Products" in the navigation
- **By Category**: Click any category link in the navigation bar (Electronics, Fashion - Men, etc.)
- **Search**: Use the search bar in the header

### Wishlist

1. **Add to Wishlist**: 
   - Click the heart icon on any product card
   - Or click "Favourite" button on product detail page
   - Requires login

2. **View Wishlist**: 
   - Click "Lists" in the header
   - Or go to `/wishlist/`

3. **Remove from Wishlist**: 
   - Click the heart icon again to remove
   - Or remove from the wishlist page

### Customer Accounts

Imported customers have:
- Email: `customer001@auroramart.com`, `customer002@auroramart.com`, etc.
- Default password: `changeme123`
- Username: `customer001`, `customer002`, etc.

**Note**: Users should change their passwords after first login.

## File Structure

```
aurora/auroramart_project/
├── adminpanel/
│   ├── management/
│   │   └── commands/
│   │       ├── import_products.py
│   │       └── import_customers.py
│   └── models.py
├── storefront/
│   ├── views.py          # Main views including auth
│   ├── models.py        # Cart, Wishlist models
│   ├── urls.py
│   └── templates/
└── auroramart_project/
    └── settings.py      # Django settings
```

## Important Notes

1. **CSV Import**: The import commands read from the `data/` folder in the project root
2. **Google OAuth**: Works only if configured with valid credentials
3. **Wishlist**: Requires user authentication
4. **Categories**: Product categories are automatically filtered based on the CSV data

## Troubleshooting

### Import Errors
- Check that CSV files are in the `data/` folder
- Verify CSV file encoding (products CSV uses latin-1 encoding)

### Google OAuth Not Working
- Verify environment variables are set
- Check redirect URI matches in Google Cloud Console
- Ensure `social-auth-app-django` is installed

### Database Issues
- Run `python manage.py makemigrations`
- Run `python manage.py migrate`

## Next Steps

To enhance the application further, consider:
- Adding product images to the media folder
- Implementing product reviews
- Adding order processing
- Enhancing the search functionality
- Adding filters (price range, rating, etc.)

