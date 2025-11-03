# How to Set Google OAuth Environment Variables (Windows)

This guide will walk you through setting up Google OAuth credentials for AuroraMart.

## Part 1: Get Google OAuth Credentials

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "AuroraMart")
5. Click **"Create"**

### Step 2: Configure OAuth Consent Screen
1. In the left sidebar, go to **"APIs & Services"** > **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace)
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: AuroraMart (or any name)
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **"Save and Continue"** through the steps
6. On the **"Scopes"** page, click **"Save and Continue"** (no changes needed)
7. On the **"Test users"** page:
   - Click **"+ ADD USERS"**
   - Add your Gmail address
   - Click **"Add"**
   - Click **"Save and Continue"**

### Step 3: Create OAuth 2.0 Credentials
1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. Choose **"Web application"** as the application type
5. Fill in:
   - **Name**: AuroraMart (or any name)
   - **Authorized redirect URIs**: 
     - Click **"+ ADD URI"**
     - Enter: `http://127.0.0.1:8000/oauth/complete/google-oauth2/`
     - Click **"ADD URI"** again and enter: `http://localhost:8000/oauth/complete/google-oauth2/`
6. Click **"CREATE"**
7. **IMPORTANT**: Copy both:
   - **Your Client ID** (looks like: `123456789-abcdefg.apps.googleusercontent.com`)
   - **Your Client Secret** (looks like: `GOCSPX-abcdefghijklmnopqrstuvwxyz`)

**Keep these safe - you'll need them in Part 2!**

---

## Part 2: Set Environment Variables (Windows)

You have **two options**: Temporary (for current session) or Permanent (system-wide).

### Option A: Temporary Setup (PowerShell - Current Session Only)

**Use this if you want to test quickly. These settings will be lost when you close PowerShell.**

1. Open **PowerShell** (as Administrator if possible)
2. Navigate to your project directory:
   ```powershell
   cd C:\Users\chloe\OneDrive\Documents\GitHub\IS2108\aurora\auroramart_project
   ```
3. Set the environment variables (replace with your actual values):
   ```powershell
   $env:GOOGLE_OAUTH2_CLIENT_ID="your-client-id-here.apps.googleusercontent.com"
   $env:GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret-here"
   ```
   **Example:**
   ```powershell
   $env:GOOGLE_OAUTH2_CLIENT_ID="123456789-abcdefg.apps.googleusercontent.com"
   $env:GOOGLE_OAUTH2_CLIENT_SECRET="GOCSPX-abcdefghijklmnopqrstuvwxyz"
   ```
4. Verify they're set:
   ```powershell
   echo $env:GOOGLE_OAUTH2_CLIENT_ID
   echo $env:GOOGLE_OAUTH2_CLIENT_SECRET
   ```
5. **In the same PowerShell window**, start your Django server:
   ```powershell
   python manage.py runserver
   ```

**Note**: If you close PowerShell and reopen it, you'll need to set the variables again.

---

### Option B: Permanent Setup (System-Wide)

**Use this if you want the settings to persist across all sessions.**

#### Method 1: Using Windows Settings (Easiest)

1. Press **Windows Key + R**
2. Type: `sysdm.cpl` and press Enter
3. Click the **"Advanced"** tab
4. Click **"Environment Variables..."** button (at the bottom)
5. Under **"User variables"** (top section), click **"New..."**
6. Add the first variable:
   - **Variable name**: `GOOGLE_OAUTH2_CLIENT_ID`
   - **Variable value**: `your-client-id-here.apps.googleusercontent.com`
   - Click **"OK"**
7. Click **"New..."** again
8. Add the second variable:
   - **Variable name**: `GOOGLE_OAUTH2_CLIENT_SECRET`
   - **Variable value**: `your-client-secret-here`
   - Click **"OK"**
9. Click **"OK"** on all dialogs to save
10. **Restart your terminal/PowerShell** for changes to take effect
11. Navigate to your project and start the server:
    ```powershell
    cd C:\Users\chloe\OneDrive\Documents\GitHub\IS2108\aurora\auroramart_project
    python manage.py runserver
    ```

#### Method 2: Using PowerShell (Permanent)

1. Open **PowerShell as Administrator**
2. Run these commands (replace with your actual values):
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GOOGLE_OAUTH2_CLIENT_ID", "your-client-id-here.apps.googleusercontent.com", "User")
   [System.Environment]::SetEnvironmentVariable("GOOGLE_OAUTH2_CLIENT_SECRET", "your-client-secret-here", "User")
   ```
3. **Close and reopen PowerShell** for changes to take effect

---

## Part 3: Verify Setup

1. Start your Django server (if not already running):
   ```powershell
   python manage.py runserver
   ```
2. Open your browser and go to: `http://127.0.0.1:8000/login/`
3. You should see the **"Continue with Google"** button
4. Click it - you should be redirected to Google's login page
5. After logging in with Google, you should be redirected back to AuroraMart

---

## Troubleshooting

### "Missing required parameter: client_id" Error
- **Solution**: Make sure you set the environment variables correctly and restarted your server
- Verify in PowerShell: `echo $env:GOOGLE_OAUTH2_CLIENT_ID`

### "Redirect URI mismatch" Error
- **Solution**: Check that the redirect URI in Google Console matches exactly:
  - `http://127.0.0.1:8000/oauth/complete/google-oauth2/`
  - No trailing slash issues, exactly as shown

### "Access blocked" Error
- **Solution**: 
  1. Go to Google Cloud Console > OAuth consent screen
  2. Make sure your email is added as a **Test user**
  3. Wait a few minutes for changes to propagate

### Environment Variables Not Working
- **Solution**: 
  - If using temporary setup, make sure you're running the server in the **same PowerShell window** where you set the variables
  - If using permanent setup, **restart your terminal/PowerShell** completely
  - Verify variables are set: `echo $env:GOOGLE_OAUTH2_CLIENT_ID` in PowerShell

### Still Not Working?
1. Check that `social-auth-app-django` is installed:
   ```powershell
   pip list | findstr social
   ```
   Should show: `social-auth-app-django`
   
2. If not installed:
   ```powershell
   pip install social-auth-app-django
   ```

---

## Quick Reference Commands

### Set Temporary (PowerShell - Current Session)
```powershell
$env:GOOGLE_OAUTH2_CLIENT_ID="your-client-id"
$env:GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret"
python manage.py runserver
```

### Verify Variables Are Set
```powershell
echo $env:GOOGLE_OAUTH2_CLIENT_ID
echo $env:GOOGLE_OAUTH2_CLIENT_SECRET
```

### Check if social-auth-app-django is Installed
```powershell
pip show social-auth-app-django
```

---

## Important Notes

- **Security**: Never commit your Client ID and Secret to Git or share them publicly
- **Development vs Production**: Use different OAuth credentials for production
- **Session Persistence**: Temporary variables only last for the current PowerShell session
- **Testing**: Make sure your Google account email is added as a test user in OAuth consent screen

---

## Need Help?

If you're still having issues:
1. Check that you copied the Client ID and Secret correctly (no extra spaces)
2. Make sure the redirect URI in Google Console matches exactly
3. Restart your Django server after setting environment variables
4. Verify your Google account is added as a test user

