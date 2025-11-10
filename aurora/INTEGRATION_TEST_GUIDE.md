# Integration Test Guide

## Changes Made

### ✅ Admin Panel Sidebar Toggle
**Files Modified:**
- `adminpanel/static/scripts/admin.js` - Rewrote sidebar toggle logic
- `adminpanel/templates/adminpanel/base.html` - Updated JS version to v2.0, CSS to v5.3

### ✅ Storefront Category Hover
**Files Modified:**
- `storefront/static/js/storefront.js` - Enhanced category panel positioning
- `storefront/static/css/storefront.css` - Fixed panel positioning and z-index
- `storefront/templates/storefront/base.html` - Updated JS to v1.5, CSS to v1.4

## HTML Structure Verification ✓

### Admin Panel (VERIFIED)
- ✅ `<aside class="sidebar" id="sidebar">` - Present
- ✅ `<button class="sidebar-toggle" id="sidebarToggle">` - Present
- ✅ `<button class="floating-toggle" id="floatingToggle">` - Present
- ✅ `<main class="main-content">` - Present
- ✅ `<script src="{% static 'scripts/admin.js' %}?v=2.0">` - Present with cache-busting

### Storefront (VERIFIED)
- ✅ `<div class="category-browser-item-wrapper" data-category-id="category-{{ forloop.counter }}">` - Present
- ✅ `<a class="category-browser-item has-subcategories">` - Present
- ✅ `<div class="category-subcategory-panels-container">` - Present
- ✅ `<div class="category-subcategory-panel" data-category-id="category-{{ forloop.counter }}">` - Present
- ✅ `<script src="{% static 'js/storefront.js' %}?v=1.5">` - Present with cache-busting

## Testing Instructions

### 1. Admin Panel Sidebar Toggle

**Test on Desktop:**
1. Navigate to any admin panel page (e.g., `/adminpanel/`)
2. Open browser DevTools Console (F12 → Console tab)
3. Look for: `"Sidebar toggle initialized"` message
4. Click the hamburger icon (☰) in the sidebar header
   - Sidebar should slide out to the left
   - Floating button should appear
   - Console should show: `"Sidebar state changed: hidden"`
5. Click the floating button
   - Sidebar should slide back in
   - Console should show: `"Sidebar state changed: visible"`
6. Refresh the page - sidebar should remember its state

**Test on Mobile/Tablet:**
1. Resize browser to < 1024px width OR use DevTools device emulation
2. Open sidebar if hidden
3. Click anywhere outside the sidebar
   - Sidebar should close automatically

**Troubleshooting:**
- If nothing happens: Check Console for JavaScript errors
- If no console messages: JS file might not be loading - check network tab
- Clear browser cache (Ctrl+Shift+Delete) and hard refresh (Ctrl+F5)

### 2. Storefront Category Hover

**Test:**
1. Navigate to product list page (`/products/` or any category page)
2. Open browser DevTools Console
3. Look for: `"Category subcategory panels initialized"` and `"Found panels: X"` messages
4. Hover over a category item that has an arrow icon (→)
   - Console should show: `"Showing panel: category-X at top: Y"`
   - Subcategory panel should appear smoothly to the right
   - Panel should have a white background with shadow
   - Category item should have teal left border
5. Move mouse over the subcategory panel
   - Panel should stay visible
   - Console should show: `"Mouse entered panel: category-X"`
6. Move mouse away from both category and panel
   - Panel should fade out after brief delay
   - Console should show: `"Hiding panel: category-X"`
7. Scroll the category sidebar while hovering
   - Panel should stay aligned with the category item

**Visual Checks:**
- Category with subcategories: Light teal background on hover
- Arrow icon: Should slide right and turn teal on hover
- Subcategory panel: Should appear at 280px from left edge
- Subcategory links: Should highlight on hover

**Troubleshooting:**
- If panels don't appear at all:
  - Check Console for: `"No category wrappers found"` or `"No panel found for category: X"`
  - Verify you're on a page with categories (product list page)
  - Check that `navigation_categories` context variable is populated
- If panels appear in wrong position:
  - Check z-index in DevTools (should be 10002)
  - Check position is `fixed` not `absolute`
- Clear browser cache and hard refresh

## Quick Diagnostics

### Check JavaScript Loading
Open DevTools Console and run:
```javascript
// Admin Panel
console.log('Sidebar:', document.getElementById('sidebar'));
console.log('Toggle Button:', document.getElementById('sidebarToggle'));

// Storefront
console.log('Category Wrappers:', document.querySelectorAll('.category-browser-item-wrapper').length);
console.log('Panels:', document.querySelectorAll('.category-subcategory-panel').length);
```

### Force Cache Refresh
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

Or use keyboard shortcut:
- **Windows/Linux:** Ctrl + Shift + Delete → Clear cache → Ctrl + F5
- **Mac:** Cmd + Shift + Delete → Clear cache → Cmd + Shift + R

## Common Issues & Solutions

### Issue: "Changes not appearing"
**Solution:** 
- Clear browser cache completely
- Check version numbers in HTML source (View Page Source):
  - Admin CSS should be `v=5.3`
  - Admin JS should be `v=2.0`
  - Storefront CSS should be `v=1.4`
  - Storefront JS should be `v=1.5`
- Do a hard refresh (Ctrl+F5 / Cmd+Shift+R)

### Issue: "Console shows no messages"
**Solution:**
- Check Network tab in DevTools
- Look for 404 errors on JS files
- Verify static files are being served
- Run `python manage.py collectstatic` if in production

### Issue: "Sidebar toggle works but looks wrong"
**Solution:**
- Check CSS is loaded (Network tab)
- Verify CSS version is v5.3
- Check for CSS conflicts in DevTools Elements tab

### Issue: "Subcategory panels appear but in wrong place"
**Solution:**
- Check CSS `.category-subcategory-panel` has `position: fixed`
- Verify `left: 280px` in CSS
- Check z-index is `10002`
- Inspect element in DevTools to see computed styles

## Expected Console Output

### Admin Panel (when working correctly):
```
Sidebar toggle initialized
Sidebar state changed: hidden
Sidebar state changed: visible
```

### Storefront (when working correctly):
```
Found panels: 5
Category subcategory panels initialized
Showing panel: category-1 at top: 250
Mouse entered panel: category-1
Hiding panel: category-1
```

## Files Changed Summary

1. `/adminpanel/static/scripts/admin.js` ✓
2. `/adminpanel/static/css/admin_styles.css` ✓
3. `/adminpanel/templates/adminpanel/base.html` ✓
4. `/storefront/static/js/storefront.js` ✓
5. `/storefront/static/css/storefront.css` ✓
6. `/storefront/templates/storefront/base.html` ✓

All files are properly linked and version-bumped for cache busting.
