# AuroraMart Admin Panel - Complete Guide

## Overview
A professional, modern admin panel for the AuroraMart e-commerce platform with comprehensive CRUD functionality, AI-driven insights, and a sleek black/white/grey color scheme.

## Features Implemented

### 🎨 Design & UI
- **Professional Sidebar Navigation**: Fixed sidebar with smooth animations and collapsible functionality
- **Modern Color Scheme**: Black (#000), white (#FFF), and grey tones for a clean, professional look
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Smooth Animations**: Transitions and hover effects throughout
- **Intuitive UX**: Clear visual hierarchy, consistent styling, and user-friendly interactions

### 📊 Dashboard (User Story #6)
**Location**: `/admin/` (index page)

**Features**:
- **KPI Cards**: Total customers, products, orders, and revenue
- **Top 3 Rated Products**: Display with star ratings and quick navigation
- **Worst 3 Rated Products**: Identify products needing attention
- **Preferred Category Pie Chart**: AI-driven customer segmentation visualization
- **Sales Overview Bar Chart**: Monthly revenue trends
- **Restock Alerts**: Products needing restock with direct links to product pages
- **Top Customers Table**: Customers by order count with purchase statistics

### 👥 Customers Page (User Story #1)
**Location**: `/admin/customers/`

**Features**:
- **Full CRUD Operations**: Create, Read, Update, Delete customers
- **AI Prediction**: Automatically predicts preferred category based on customer profile
- **Advanced Filtering**: Search, category, age range, income range
- **Sorting**: Multiple sort options (name, email, age, income, etc.)
- **Modal Form**: Clean popup form for creating new customers
- **Detailed View**: Edit customer information with full form validation

### 📦 Products Page (User Story #2)
**Location**: `/admin/products/`

**Features**:
- **Full CRUD Operations**: Complete product management
- **Advanced Filtering**: Search, category, subcategory, price range, rating, stock status
- **Multiple Sort Options**: Name, SKU, price, rating, stock level
- **Image Upload**: Product image management with preview
- **Stock Alerts**: Visual indicators for low/out of stock items
- **Star Ratings**: Visual rating display
- **Status Indicators**: Active/inactive badges

### 📋 Catalogue Page (User Story #3)
**Location**: `/admin/catalogue/`

**Features**:
- **Product Visibility Control**: Toggle products on/off for storefront
- **Grid View**: Visual product cards with images
- **Toggle Switches**: Smooth on/off switches for each product
- **Bulk Actions**: Activate/deactivate multiple products at once
- **Statistics**: Real-time counts of total, active, and inactive products
- **Filter Options**: Search, category, and status filters

### 🛒 Orders Page (User Story #4)
**Location**: `/admin/orders/`

**Features**:
- **Full CRUD Operations**: Complete order management
- **Order Items Management**: Add/edit/delete products within orders
- **Auto-calculation**: Total amount calculated automatically from line items
- **Advanced Filtering**: Customer, status, date range, amount range
- **Relational Data**: Proper database relationships between orders, customers, and products
- **Status Management**: Track order fulfillment (Pending, Processing, Shipped, Delivered, Cancelled)
- **Detailed Order View**: Full order breakdown with line items and totals

### 👤 Admin Users Page (User Story #5)
**Location**: `/admin/admin-users/` (Superuser only)

**Features**:
- **Superuser Access Only**: admin/admin credentials required
- **Create Admin Users**: Add new staff members with login access
- **User Management**: View all admins and superusers
- **Delete Admins**: Remove admin users (cannot delete main admin)
- **Security**: Password validation and secure authentication
- **Role Display**: Clear distinction between superusers and regular admins

### 🔐 Authentication (User Story #5 & #7)
**Login**: `/admin/login/`
**Logout**: `/admin/logout/`

**Features**:
- **Secure Login**: Django's built-in authentication system
- **Beautiful Auth Pages**: Dedicated login/logout pages with AuroraMart branding
- **Session Management**: Secure session handling
- **Logout Options**: Navigate to customer site or admin login after logout
- **Default Credentials**: admin / admin (as specified)

## Technology Stack

### Backend
- Django 5.2.8
- Python 3.13
- SQLite Database
- joblib (for ML model integration)

### Frontend
- Vanilla JavaScript (no framework dependencies)
- CSS3 with custom properties
- Font Awesome 6.4.0 icons
- Chart.js for data visualization

### Key Files Created

```
adminpanel/
├── templates/adminpanel/
│   ├── base.html                    # Base template with sidebar navigation
│   ├── index.html                   # Dashboard with KPIs and charts
│   ├── customer_list.html           # Customer management with CRUD
│   ├── customer_detail.html         # Customer edit page
│   ├── product_list.html            # Product management with CRUD
│   ├── product_detail.html          # Product edit page
│   ├── catalogue.html               # Product visibility control
│   ├── order_list.html              # Order management with CRUD
│   ├── order_detail.html            # Order edit with line items
│   ├── admin_users_list.html        # Admin user management (superuser only)
│   ├── login.html                   # Admin login page
│   └── logout.html                  # Logout confirmation page
├── static/
│   ├── css/
│   │   └── admin_styles.css         # Comprehensive styling (21KB)
│   ├── scripts/
│   │   └── admin.js                 # Interactive features (14KB)
│   └── images/
│       └── AuroraMart Logo.png      # Brand logo
├── models.py                         # Database models (existing)
├── views.py                          # View logic (existing)
├── forms.py                          # Form definitions (existing)
└── urls.py                           # URL routing (existing)
```

## CSS Architecture

The CSS follows Object-Oriented principles with:

### Variables (CSS Custom Properties)
- Color scheme variables
- Spacing and sizing variables
- Transition speeds
- Border radius and shadows

### Component Classes
- `.btn-*` - Button variants
- `.card-*` - Card components
- `.form-*` - Form elements
- `.badge-*` - Status badges
- `.alert-*` - Notification alerts
- `.stat-card` - Dashboard statistics
- `.table-*` - Table components
- `.modal-*` - Modal dialogs

### Layout Classes
- `.dashboard-grid` - Responsive grid for KPIs
- `.form-grid` - Form layout grid
- `.filter-bar` - Filter section layout
- `.product-grid` - Product card grid

### Utility Classes
- Text alignment, colors, spacing
- Flexbox helpers
- Responsive utilities

## JavaScript Features

### Core Functionality
- **Sidebar Toggle**: Collapsible sidebar with localStorage persistence
- **Modal System**: Reusable modal dialogs
- **Form Validation**: Client-side validation
- **AJAX Operations**: Toggle switches, bulk actions
- **Notifications**: Toast-style notifications
- **Confirmation Dialogs**: Delete confirmations

### Interactive Features
- Auto-hiding alerts (5 seconds)
- Live search with debouncing
- Image preview for uploads
- Dynamic formsets for order items
- Keyboard shortcuts (Ctrl/Cmd + K for search)
- CSV export functionality
- Print support

## Usage Instructions

### 1. Start the Server
```bash
cd /Users/justin/Documents/GitHub/IS2108/auroramart_project/auroramart_project
python manage.py runserver
```

### 2. Access the Admin Panel
- URL: http://127.0.0.1:8000/admin/
- Username: `admin`
- Password: `admin`

### 3. Navigation
The sidebar provides access to all main sections:
- **Dashboard**: Overview and analytics
- **Customers**: Customer management
- **Products**: Product catalog management
- **Catalogue**: Product visibility control
- **Orders**: Order processing
- **Admin Users**: User management (superuser only)
- **Logout**: Sign out

### 4. Common Operations

#### Create a Customer
1. Navigate to Customers page
2. Click "Add Customer" button
3. Fill in the form (preferred category is AI-predicted)
4. Click "Create Customer"

#### Manage Products
1. Navigate to Products page
2. Use filters to find products
3. Click edit icon to modify
4. Click delete icon to remove (with confirmation)

#### Control Catalogue Visibility
1. Navigate to Catalogue page
2. Use toggle switches to show/hide products
3. Or select multiple and use bulk actions

#### Process Orders
1. Navigate to Orders page
2. Click "Create Order" to add new order
3. Select customer and status
4. Add order items (product + quantity)
5. Total is calculated automatically

#### Manage Admin Users (Superuser Only)
1. Navigate to Admin Users page
2. Click "Add Admin User"
3. Fill in credentials
4. New admin can now log in

## Responsive Breakpoints

- **Desktop**: Full sidebar and layout (> 1024px)
- **Tablet**: Collapsed sidebar (768px - 1024px)
- **Mobile**: Optimized layout (< 768px)

## Security Features

- CSRF protection on all forms
- User authentication required
- Superuser restrictions for admin management
- Cannot delete yourself
- Cannot delete main admin account
- Secure password hashing
- Session management

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Modern browsers with ES6+ support

## Performance Optimizations

- Efficient CSS with minimal specificity
- Debounced search inputs
- Lazy loading where applicable
- Optimized database queries
- Cached static files

## Design Principles

### Color Psychology
- **Black**: Authority, professionalism, sophistication
- **White**: Clarity, simplicity, cleanliness
- **Grey**: Balance, neutrality, modern aesthetic

### Typography
- Primary Font: Segoe UI (system font for performance)
- Clear hierarchy with font sizes
- Readable line height (1.6)
- Proper contrast ratios for accessibility

### Spacing
- Consistent padding and margins
- Visual breathing room
- Clear component boundaries

### Interactions
- Hover effects on interactive elements
- Smooth transitions (0.3s)
- Clear focus states
- Loading indicators

## AI Integration

### Customer Category Prediction
- Uses Decision Tree Classifier
- Trained on customer demographics
- Automatic prediction on customer creation
- 22 features including age, income, education, etc.

### Dashboard Analytics
- Customer segmentation pie chart
- Product ratings analysis
- Sales trends visualization
- Inventory alerts

## Future Enhancements

Potential additions:
- Export reports to PDF
- Email notifications
- Advanced analytics dashboard
- Real-time inventory updates
- Customer communication tools
- Order tracking integration
- Multi-language support
- Dark mode toggle

## Troubleshooting

### Static Files Not Loading
```bash
python manage.py collectstatic
```

### Database Issues
```bash
python manage.py migrate
python manage.py makemigrations
```

### Admin User Not Working
```bash
python manage.py createsuperuser
# Follow prompts to create admin user
```

### ML Model Warnings
The sklearn version warnings are informational only and don't affect functionality.

## Support

For issues or questions:
1. Check browser console for JavaScript errors
2. Check Django logs for backend errors
3. Verify all migrations are applied
4. Ensure static files are collected
5. Confirm database has data

## Credits

Built with Django, Chart.js, Font Awesome, and modern web technologies.
Designed for AuroraMart e-commerce platform with professional admin panel requirements.

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**License**: Proprietary - AuroraMart

