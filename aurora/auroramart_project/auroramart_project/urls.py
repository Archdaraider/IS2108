"""
URL configuration for auroramart_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Keep the default Django Admin for system management/superusers
    path('django-admin/', admin.site.urls), 
    path('admin/', include('adminpanel.urls')), 
    path('', include('storefront.urls')),
]

# Add Social Auth URLs (Google OAuth) - always include if social_django is installed
# Must be added BEFORE the storefront URLs to avoid conflicts
try:
    import social_django
    urlpatterns.insert(0, path('oauth/', include('social_django.urls', namespace='social')))
except ImportError:
    pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: STATIC files are automatically served by Django's runserver in DEBUG mode