# Banner Management System

## Overview
The AuroraMart admin panel now includes a complete banner management system that allows you to upload, view, and delete advertisement banners that appear on the storefront homepage carousel.

## Features

### Admin Panel Features
- **Upload Banners**: Upload banner images with optional links and ordering
- **View All Banners**: Grid view of all banners with preview images
- **Toggle Active Status**: Enable/disable banners without deleting them
- **Delete Banners**: Remove banners and their associated images
- **Order Management**: Control the display order of banners

### Storefront Integration
- Banners automatically appear in the homepage hero carousel
- Active banners are displayed based on their order
- Clickable banners redirect to specified URLs (if provided)
- Fallback to static banners if no database banners exist

## How to Use

### Uploading a Banner

1. Navigate to **Banners** in the admin panel sidebar
2. Click **Upload New Banner**
3. Fill in the form:
   - **Banner Title** (required): A descriptive name for internal use
   - **Banner Image** (required): Upload image file (recommended: 1920x500px)
   - **Link URL** (optional): URL to redirect when banner is clicked
   - **Display Order**: Lower numbers appear first (0 = highest priority)
   - **Show banner on storefront**: Check to make banner active immediately
4. Click **Upload Banner**

### Managing Banners

1. Go to **Banners** in the admin panel
2. View all banners in a grid layout
3. Each banner card shows:
   - Preview image
   - Title
   - Order number
   - Active/Inactive status badge
4. Actions available:
   - **Toggle Switch**: Enable/disable banner
   - **Delete Button**: Remove banner permanently

### Banner Display Order

- Banners are displayed based on the **order** field (ascending)
- Lower order numbers appear first in the carousel
- Example: Order 0 → Order 1 → Order 2
- If multiple banners have the same order, newest banners appear first

## Technical Details

### Database Model
Location: `adminpanel/models.py`

```python
class Banner(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Image Storage
- Banner images are stored in: `media/banners/`
- Recommended image size: 1920x500 pixels
- Supported formats: JPG, PNG, GIF, WebP

### URLs
- List view: `/adminpanel/banners/`
- Upload form: `/adminpanel/banners/upload/`
- Delete: `/adminpanel/banners/<id>/delete/`
- Toggle active: `/adminpanel/banners/<id>/toggle/`

### Templates
- List view: `adminpanel/templates/adminpanel/banner_list.html`
- Upload form: `adminpanel/templates/adminpanel/banner_upload.html`

### Views
Location: `adminpanel/views.py`
- `banner_list()`: Display all banners
- `banner_upload()`: Upload form and processing
- `banner_delete()`: Delete banner and image file
- `banner_toggle_active()`: AJAX toggle for active status

## Integration with Storefront

The storefront homepage (`storefront/views.py` - `homepage()` function) automatically:
1. Fetches active banners from the database
2. Orders them by the `order` field
3. Passes them to the homepage template
4. Falls back to static banner images if no database banners exist

Template: `storefront/templates/storefront/homepage.html`
- Displays banners in a carousel
- Shows navigation arrows if multiple banners exist
- Auto-rotates every 5 seconds
- Supports click-through URLs

## Tips

1. **Image Size**: Use 1920x500px images for best results across devices
2. **File Size**: Optimize images to under 500KB for faster loading
3. **Order Strategy**: Use increments of 10 (0, 10, 20) to easily insert banners later
4. **Testing**: Toggle banners inactive instead of deleting to preserve them
5. **Mobile**: Images are automatically scaled for mobile devices

## Future Enhancements

Potential improvements:
- Bulk upload multiple banners
- Schedule banners for specific dates
- Analytics tracking for banner clicks
- A/B testing capabilities
- Category-specific banners
- Mobile-specific banner images
