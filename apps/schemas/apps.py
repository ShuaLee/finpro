from django.apps import AppConfig


class SchemasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schemas'
    verbose_name = 'Portfolio Schemas'

    def ready(self):
        # We are not using signals now because logic is handled in services
        # But if needed in future, import signals here
        pass
