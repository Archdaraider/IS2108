# Google OAuth Setup for Team Members

## Quick Setup (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Your `.env` File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```
   
   Or manually create a file named `.env` in the `auroramart_project` folder.

2. Open `.env` and add your Google OAuth credentials:
   ```
   GOOGLE_OAUTH2_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret-here
   ```

### Step 3: Get Your Google OAuth Credentials

**You need your own Google Cloud credentials** (each developer needs their own):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Go to **APIs & Services** > **OAuth consent screen**
   - Choose **External**
   - Add your email as a test user
4. Go to **APIs & Services** > **Credentials**
   - Click **+ CREATE CREDENTIALS** > **OAuth client ID**
   - Choose **Web application**
   - Add redirect URI: `http://127.0.0.1:8000/oauth/complete/google-oauth2/`
   - Copy your **Client ID** and **Client Secret**
5. Paste them into your `.env` file

**That's it!** The app will automatically read from your `.env` file.

## Detailed Instructions

See `SET_GOOGLE_OAUTH_ENV.md` for step-by-step screenshots and detailed instructions.

## Important Notes

- ✅ The `.env` file is already in `.gitignore` - your credentials won't be committed
- ✅ Each developer needs their own Google OAuth credentials
- ✅ The `.env.example` file is a template - create your own `.env` from it
- ✅ No code changes needed - just add your credentials to `.env`

