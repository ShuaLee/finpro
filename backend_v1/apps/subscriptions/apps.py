"""
subscriptions.apps
~~~~~~~~~~~~~~~~~~~
App configuration for the Subscriptions app.

Responsibilities:
- Ensure default plans exist when the application starts.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        from .signals import create_default_plans
        post_migrate.connect(
            create_default_plans, sender=self)
