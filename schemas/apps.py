from django.apps import AppConfig


class SchemasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schemas'

    def ready(self):
        import schemas.signals
