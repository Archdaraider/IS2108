# Google OAuth Setup Instructions

## Error: Missing required parameter: client_id

This error occurs because Google OAuth credentials are not configured. Follow these steps:

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. If prompted, configure the OAuth consent screen first:
   - Choose **External** user type
   - Fill in required fields (App name, User support email, etc.)
   - Add your email as a test user
6. For OAuth client ID:
   - Application type: **Web application**
   - Name: AuroraMart (or any name)
   - **Authorized redirect URIs**: Add these:
     - `http://127.0.0.1:8000/oauth/complete/google-oauth2/` (for development)
     - `http://localhost:8000/oauth/complete/google-oauth2/` (alternative)
     - For production, add: `https://yourdomain.com/oauth/complete/google-oauth2/`
7. Click **Create**
8. Copy the **Client ID** and **Client Secret**

### Step 2: Set Environment Variables

**Windows PowerShell:**
```powershell
$env:GOOGLE_OAUTH2_CLIENT_ID="your-client-id-here"
$env:GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret-here"
```

**Windows Command Prompt:**
```cmd
set GOOGLE_OAUTH2_CLIENT_ID=your-client-id-here
set GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret-here
```

**For permanent setup (Windows):**
1. Open System Properties > Environment Variables
2. Add new User variables:
   - Variable: `GOOGLE_OAUTH2_CLIENT_ID`, Value: `your-client-id`
   - Variable: `GOOGLE_OAUTH2_CLIENT_SECRET`, Value: `your-client-secret`

**Linux/Mac:**
```bash
export GOOGLE_OAUTH2_CLIENT_ID="your-client-id-here"
export GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret-here"
```

Or add to `~/.bashrc` or `~/.zshrc`:
```bash
export GOOGLE_OAUTH2_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret"
```

### Step 3: Restart Django Server

After setting environment variables, restart your Django development server:
```bash
python manage.py runserver
```

### Step 4: Test Google Login

1. Go to `/login/` or `/register/`
2. Click "Continue with Google"
3. You should be redirected to Google's login page
4. After authentication, you'll be redirected back to the site

### Troubleshooting

- **Error 400: invalid_request** - Check that redirect URI matches exactly in Google Console
- **Access blocked** - Ensure OAuth consent screen is configured and your email is added as a test user
- **Redirect URI mismatch** - Verify the redirect URI in Google Console matches: `http://127.0.0.1:8000/oauth/complete/google-oauth2/`

### Note

If you don't want to set up Google OAuth, the application will still work with email/password authentication. The Google OAuth buttons simply won't appear if credentials are not configured.

