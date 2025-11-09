"""
Quick test to verify Google OAuth configuration is working
"""
import os
import sys
import django

# Set up Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auroramart_project.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("Google OAuth Configuration Test")
print("=" * 60)
print()

client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

print(f"Client ID found: {'✓ YES' if client_id else '✗ NO'}")
if client_id:
    print(f"  → {client_id[:50]}...")

print(f"\nClient Secret found: {'✓ YES' if client_secret else '✗ NO'}")

backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
oauth_enabled = 'social_core.backends.google.GoogleOAuth2' in backends

print(f"\nGoogle OAuth Backend enabled: {'✓ YES' if oauth_enabled else '✗ NO'}")

if client_id and client_secret and oauth_enabled:
    print("\n" + "=" * 60)
    print("✓ Google OAuth is properly configured!")
    print("=" * 60)
    print("\nYou can now use Google login/signup.")
else:
    print("\n" + "=" * 60)
    print("✗ Google OAuth is NOT properly configured")
    print("=" * 60)
    if not client_id or not client_secret:
        print("\nMissing credentials. Check your .env file:")
        print("  - Location: aurora/auroramart_project/.env")
        print("  - Should contain:")
        print("    GOOGLE_OAUTH2_CLIENT_ID=your-client-id")
        print("    GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret")

