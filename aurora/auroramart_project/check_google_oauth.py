"""
Helper script to check Google OAuth configuration
Run this to diagnose Google OAuth setup issues
"""
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 60)
print("Google OAuth Configuration Checker")
print("=" * 60)
print()

# Check 1: Is social_django installed?
print("1. Checking if social-auth-app-django is installed...")
try:
    import social_django
    print("   ✓ social-auth-app-django is installed")
except ImportError:
    print("   ✗ social-auth-app-django is NOT installed")
    print("   → Install it with: pip install social-auth-app-django")
    sys.exit(1)

# Check 2: Is python-decouple installed?
print("\n2. Checking if python-decouple is installed...")
try:
    from decouple import config
    print("   ✓ python-decouple is installed")
except ImportError:
    print("   ✗ python-decouple is NOT installed")
    print("   → Install it with: pip install python-decouple")
    sys.exit(1)

# Check 3: Check for .env file
print("\n3. Checking for .env file...")
env_file = BASE_DIR / '.env'
if env_file.exists():
    print(f"   ✓ .env file found at: {env_file}")
    # Try to read credentials from .env
    try:
        from decouple import config
        client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
        client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
        
        if client_id and client_secret:
            print("   ✓ Credentials found in .env file")
            print(f"   → Client ID: {client_id[:30]}...")
        else:
            print("   ✗ Credentials NOT found in .env file")
            print("   → Add these lines to .env:")
            print("     GOOGLE_OAUTH2_CLIENT_ID=your-client-id")
            print("     GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret")
    except Exception as e:
        print(f"   ✗ Error reading .env file: {e}")
else:
    print(f"   ✗ .env file NOT found at: {env_file}")
    print("   → Create a .env file in the project root with:")
    print("     GOOGLE_OAUTH2_CLIENT_ID=your-client-id")
    print("     GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret")

# Check 4: Check environment variables
print("\n4. Checking environment variables...")
client_id_env = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID', '')
client_secret_env = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET', '')

if client_id_env and client_secret_env:
    print("   ✓ Credentials found in environment variables")
    print(f"   → Client ID: {client_id_env[:30]}...")
else:
    print("   ✗ Credentials NOT found in environment variables")
    print("   → Set them with:")
    print("     PowerShell: $env:GOOGLE_OAUTH2_CLIENT_ID='your-id'")
    print("     CMD: set GOOGLE_OAUTH2_CLIENT_ID=your-id")

# Check 5: Try to load from Django settings
print("\n5. Checking Django settings...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auroramart_project.settings')
    import django
    django.setup()
    
    from django.conf import settings
    
    # Check if social_django is in INSTALLED_APPS
    if 'social_django' in settings.INSTALLED_APPS:
        print("   ✓ social_django is in INSTALLED_APPS")
    else:
        print("   ✗ social_django is NOT in INSTALLED_APPS")
    
    # Check credentials
    client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
    client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
    
    if client_id and client_secret:
        print("   ✓ Google OAuth credentials are configured in Django settings")
        print(f"   → Client ID: {client_id[:30]}...")
        
        # Check if OAuth backend is enabled
        backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
        if 'social_core.backends.google.GoogleOAuth2' in backends:
            print("   ✓ Google OAuth backend is enabled")
            print("\n" + "=" * 60)
            print("✓ Google OAuth is properly configured!")
            print("=" * 60)
        else:
            print("   ✗ Google OAuth backend is NOT enabled")
            print("   → This might be because credentials are empty")
    else:
        print("   ✗ Google OAuth credentials are NOT configured")
        print("   → Set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET")
        
except Exception as e:
    print(f"   ✗ Error loading Django settings: {e}")
    print("   → Make sure you're running this from the project root")

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
print("To fix Google OAuth:")
print("1. Get credentials from: https://console.cloud.google.com/apis/credentials")
print("2. Create a .env file in the project root with your credentials")
print("3. Restart your Django server")
print("=" * 60)

