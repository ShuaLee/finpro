"""
subscriptions.apps
~~~~~~~~~~~~~~~~~~~
App configuration for the Subscriptions app.

Responsibilities:
- Ensure default plans exist when the application starts.
"""

import logging
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        """
        Called when Django starts up.

        Ensures that default subscription plans (Free, Premium) exist in the database.
        If the database is not ready (e.g., during initial migration), it logs a warning
        instead of raising an error.

        Why:
            - Guarantees Free and Premium plans exist without requiring a manual script.
            - Idempotent: Will not create duplicates.
        """
        try:
            from subscriptions.models import Plan

            defaults = [
                {
                    "slug": "free",
                    "name": "Free",
                    "description": "Basic plan with limited features",
                    "max_stocks": 10,
                    "allow_crypto": False,
                    "allow_metals": False,
                    "price_per_month": 0.00,
                },
                {
                    "slug": "premium",
                    "name": "Premium",
                    "description": "Unlimited access with crypto and metals",
                    "max_stocks": 9999,
                    "allow_crypto": True,
                    "allow_metals": True,
                    "price_per_month": 9.99,
                },
            ]

            for plan_data in defaults:
                obj, created = Plan.objects.get_or_create(
                    slug=plan_data["slug"], defaults=plan_data
                )
                if created:
                    logger.info(f"Created default plan: {obj.name}")
                else:
                    logger.debug(f"Default plan already exists: {obj.name}")

        except (OperationalError, ProgrammingError):
            # Happens when DB tables don't exist (e.g., during migrate)
            logger.warning(
                "SubscriptionsConfig.ready() skipped: Database not ready yet.")
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error while ensuring default plans: {e}")
