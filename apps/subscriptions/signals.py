"""
subscriptions.signals
~~~~~~~~~~~~~~~~~~~~~~

Defines signal handlers for the Subscriptions app.

Responsibilities:
- Create default subscription plans and account types after migrations are applied.
- Ensure database initialization logic runs safely and only after schema setup.

Why:
- Avoids performing database operations in AppConfig.ready() (which runs too early).
- Guarantees required defaults (e.g., Free plan, Premium plan, account types) exist for proper app functionality.

Implementation Details:
- Connected via Django's `post_migrate` signal in `apps.py`.
- Wrapped in a single atomic transaction for data consistency.
- Idempotent: uses `get_or_create()` to prevent duplicates on repeated runs.

Usage:
- Triggered automatically after `python manage.py migrate` or when migrations are applied during deployment.
"""

from django.db import transaction
import logging
from subscriptions.models import Plan, AccountType


def create_default_plans_and_account_types(sender, **kwargs):
    """
    Create default plans and account types after migrations.
    Runs in a single atomic transaction for consistency.
    """
    plans = [
        {"slug": "free", "name": "Free", "description": "Basic plan", "max_stocks": 10,
            "allow_crypto": False, "allow_metals": False, "price_per_month": 0.00},
        {"slug": "premium", "name": "Premium", "description": "Unlimited access",
            "max_stocks": 9999, "allow_crypto": True, "allow_metals": True, "price_per_month": 9.99},
    ]
    account_types = [
        {"slug": "individual", "name": "Individual Investor",
            "description": "For personal investment tracking."},
        {"slug": "manager", "name": "Manager",
            "description": "For managing investments on behalf of clients."},
    ]

    with transaction.atomic():
        for data in plans:
            obj, created = Plan.objects.get_or_create(
                slug=data["slug"], defaults=data)

        for data in account_types:
            obj, created = AccountType.objects.get_or_create(
                slug=data["slug"], defaults=data)
