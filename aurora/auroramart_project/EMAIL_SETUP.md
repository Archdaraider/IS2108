# Email Configuration for Password Reset

This guide will help you set up email functionality so that password reset emails are actually sent to users.

## Option 1: Gmail (Recommended for Development)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled

### Step 2: Generate an App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "AuroraMart Django" as the name
4. Click "Generate"
5. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

### Step 3: Add to .env file
Add these lines to your `.env` file in the `auroramart_project` folder:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=noreply@auroramart.com
```

**Important:**
- Replace `your-email@gmail.com` with your actual Gmail address
- Replace `abcdefghijklmnop` with the app password you generated (remove spaces)
- The app password is 16 characters without spaces

### Step 4: Restart Django Server
After updating the `.env` file, restart your Django development server:
```bash
python manage.py runserver
```

You should see: `Email configured: Using SMTP (smtp.gmail.com)`

## Option 2: Other Email Providers

### Outlook/Office 365
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@auroramart.com
```

### Yahoo Mail
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@auroramart.com
```

**Note:** Yahoo also requires an app password. Generate it at: https://login.yahoo.com/account/security

### Custom SMTP Server
```env
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@auroramart.com
```

## Testing

1. Go to: http://127.0.0.1:8000/password-reset/
2. Enter an email address that exists in your database
3. Check the email inbox (and spam folder)
4. Click the reset link in the email
5. Set a new password

## Troubleshooting

### Emails not sending
- Check that all environment variables are set correctly in `.env`
- Verify the email and password are correct
- For Gmail: Make sure you're using an App Password, not your regular password
- Check the Django console for error messages

### "Authentication failed" error
- For Gmail: Make sure 2-Factor Authentication is enabled and you're using an App Password
- Verify the email address and password are correct
- Check that "Less secure app access" is not required (Gmail no longer supports this)

### Emails going to spam
- This is normal for development. In production, set up SPF, DKIM, and DMARC records
- Check your spam folder

## Development vs Production

- **Development**: Console backend (prints to terminal) - works without configuration
- **Production**: SMTP backend - requires proper email server configuration

The system automatically uses console backend if email credentials are not provided, so the app will still work for development.

