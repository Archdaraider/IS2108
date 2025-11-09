# 🚀 Quick Start Guide - AuroraMart Merged Project

## ✅ Merge Status: COMPLETE

All merge conflicts have been resolved! Your adminpanel and your teammate's storefront are now fully integrated.

---

## 🏃 Run the Project

### 1. Navigate to Project Directory
```bash
cd /Users/justin/Documents/GitHub/IS2108/aurora/auroramart_project
```

### 2. Start the Development Server
```bash
python3 manage.py runserver
```

### 3. Access the Applications
- **Admin Panel:** http://localhost:8000/adminpanel/
- **Storefront:** http://localhost:8000/
- **Django Admin:** http://localhost:8000/admin/

---

## 🔐 Admin Login

If you need to create/setup an admin user:

```bash
# Option 1: Use your custom setup command
python3 manage.py setup_admin

# Option 2: Create a superuser manually
python3 manage.py createsuperuser
```

Default admin credentials (if using setup_admin):
- Username: `admin`
- Password: `admin`

---

## 📦 Project Structure

```
auroramart_project/
├── adminpanel/          ← YOUR WORK (Admin Dashboard, CRUD, Analytics)
├── storefront/          ← TEAMMATE'S WORK (Customer Site, Cart, Reviews)
├── auroramart_project/  ← Django Settings
├── manage.py
└── db.sqlite3
```

---

## 🔍 Verify Everything Works

### Check for Issues
```bash
python3 manage.py check
```
**Expected Output:** `System check identified no issues (0 silenced).` ✅

### View Migration Status
```bash
python3 manage.py showmigrations
```
**Expected:** All migrations should have `[X]` (applied) ✅

### Run Migrations (if needed)
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

---

## 🛠️ Common Commands

### Database
```bash
# Apply migrations
python3 manage.py migrate

# Create new migrations
python3 manage.py makemigrations

# Open database shell
python3 manage.py dbshell
```

### Static Files
```bash
# Collect static files (for production)
python3 manage.py collectstatic
```

### Development
```bash
# Run server
python3 manage.py runserver

# Run server on specific port
python3 manage.py runserver 8080

# Run on all interfaces
python3 manage.py runserver 0.0.0.0:8000
```

---

## ⚠️ Optional: Install Missing Dependencies

If you want Google OAuth and better config management:

```bash
pip install python-decouple social-auth-app-django
```

**Note:** The project works fine without these! They're optional features.

---

## 🎯 What Was Fixed

1. ✅ **Removed duplicate nested folders**
   - Deleted old `auroramart_project/adminpanel/`
   - Deleted old `auroramart_project/storefront/`
   - Deleted nested `auroramart_project/auroramart_project/`

2. ✅ **Fixed dependency issues**
   - Made `python-decouple` optional
   - Project now works with or without it

3. ✅ **Applied pending migrations**
   - All 4 pending adminpanel migrations applied
   - Database is fully synced

4. ✅ **Verified model compatibility**
   - No conflicts between adminpanel and storefront models
   - All foreign key relationships are valid

---

## 📝 Notes

### Warnings (Expected in Development)
You may see these warnings - they're normal for development:
- `Note: python-decouple not installed` - Optional dependency
- `Note: social_django not installed` - Optional Google OAuth
- `Email not configured` - Emails will print to console instead
- `WARNING: Product association rules file not found` - Optional ML feature

### Before Production Deployment
- Set `DEBUG = False` in settings.py
- Configure `ALLOWED_HOSTS`
- Set up proper `SECRET_KEY`
- Enable HTTPS/SSL settings
- Configure proper database (PostgreSQL/MySQL instead of SQLite)
- Set up proper email backend

---

## 🎉 You're All Set!

The project is ready to run. For detailed information about what was fixed, see `MERGE_FIX_SUMMARY.md`.

**Start the server:**
```bash
python3 manage.py runserver
```

Then visit: http://localhost:8000/adminpanel/

---

**Questions?** Check the comprehensive `MERGE_FIX_SUMMARY.md` for full details!

