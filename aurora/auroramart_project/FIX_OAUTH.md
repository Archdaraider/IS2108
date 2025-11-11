# Quick Fix for Google OAuth

## Problem
Your `.env` file exists with credentials, but `python-decouple` is not installed in your virtual environment, so the `.env` file is not being read.

## Solution

### Step 1: Install python-decouple in your venv

Make sure your virtual environment is activated (you should see `(venv)` in your terminal), then run:

```powershell
pip install python-decouple
```

Or if that doesn't work:
```powershell
python -m pip install python-decouple
```

### Step 2: Verify .env file location

Your `.env` file should be in: `aurora/auroramart_project/.env`

It should contain:
```
GOOGLE_OAUTH2_CLIENT_ID=594433024623-9hf4vi08g3d73qj3j3jmtp4bje7vh4pd.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=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
```

✅ Your `.env` file already has the correct credentials!

### Step 3: Restart Django Server

After installing `python-decouple`, **restart your Django server**:
1. Stop the server (Ctrl+C)
2. Start it again: `python manage.py runserver`

### Step 4: Verify

After restarting, you should see in the server output:
```
✓ Google OAuth backend configured with credentials
```

Instead of:
```
Warning: Google OAuth credentials not set...
```

Then test the OAuth login again - it should work!

## Alternative: Use Environment Variables

If `.env` still doesn't work, you can set environment variables directly in PowerShell:

```powershell
$env:GOOGLE_OAUTH2_CLIENT_ID="594433024623-9hf4vi08g3d73qj3j3jmtp4bje7vh4pd.apps.googleusercontent.com"
$env:GOOGLE_OAUTH2_CLIENT_SECRET="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"
python manage.py runserver
```

## Summary

The issue is: **python-decouple is not installed in your venv**
The fix is: **Install it with `pip install python-decouple` in your activated venv**

