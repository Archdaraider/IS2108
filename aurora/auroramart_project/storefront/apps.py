from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storefront'

    def ready(self):
        """Import signals when the app is ready."""
        import storefront.signals  # noqa