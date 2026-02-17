"""
subscriptions.signals
~~~~~~~~~~~~~~~~~~~~~~

Defines signal handlers for the Subscriptions app.

Responsibilities:
- Create default subscription plans after migrations are applied.
- Ensure database initialization logic runs safely and only after schema setup.

Why:
- Avoids performing database operations in AppConfig.ready() (which runs too early).
- Guarantees required default plans exist for proper app functionality.

Implementation Details:
- Connected via Django's `post_migrate` signal in `apps.py`.
- Wrapped in a single atomic transaction for data consistency.
- Idempotent: uses `get_or_create()` to prevent duplicates on repeated runs.

Usage:
- Triggered automatically after `python manage.py migrate` or when migrations are applied during deployment.
"""

from django.db import transaction

from subscriptions.models import Plan


def create_default_plans(sender, **kwargs):
    plans = [
        {
            "slug": "free",
            "name": "Free",
            "tier": Plan.Tier.FREE,
            "description": "Starter plan for learning your baseline allocation.",
            "max_stocks": 10,
            "allow_crypto": True,
            "allow_metals": True,
            "max_portfolios": 1,
            "max_accounts_total": 3,
            "max_equity_accounts": 1,
            "max_holdings_total": 25,
            "max_stock_holdings": 10,
            "max_crypto_holdings": 1,
            "max_real_estate_holdings": 1,
            "custom_assets_enabled": False,
            "custom_asset_types_enabled": False,
            "custom_schemas_enabled": False,
            "advanced_analytics_enabled": False,
            "allocations_enabled": False,
            "client_mode_enabled": False,
            "team_members_enabled": False,
            "price_per_month": 0.00,
            "is_active": True,
            "is_public": True,
        },
        {
            "slug": "pro",
            "name": "Pro",
            "tier": Plan.Tier.PRO,
            "description": "Advanced individual plan with broad limits.",
            "max_stocks": 1000,
            "allow_crypto": True,
            "allow_metals": True,
            "max_portfolios": 3,
            "max_accounts_total": 20,
            "max_equity_accounts": None,
            "max_holdings_total": 1000,
            "max_stock_holdings": None,
            "max_crypto_holdings": None,
            "max_real_estate_holdings": None,
            "custom_assets_enabled": True,
            "custom_asset_types_enabled": False,
            "custom_schemas_enabled": True,
            "advanced_analytics_enabled": True,
            "allocations_enabled": True,
            "client_mode_enabled": False,
            "team_members_enabled": False,
            "price_per_month": 14.99,
            "is_active": True,
            "is_public": True,
        },
        {
            "slug": "wealth-manager",
            "name": "Wealth Manager",
            "tier": Plan.Tier.WEALTH_MANAGER,
            "description": "For client-level portfolio oversight and scale.",
            "max_stocks": 100000,
            "allow_crypto": True,
            "allow_metals": True,
            "max_portfolios": 200,
            "max_accounts_total": None,
            "max_equity_accounts": None,
            "max_holdings_total": None,
            "max_stock_holdings": None,
            "max_crypto_holdings": None,
            "max_real_estate_holdings": None,
            "custom_assets_enabled": True,
            "custom_asset_types_enabled": True,
            "custom_schemas_enabled": True,
            "advanced_analytics_enabled": True,
            "allocations_enabled": True,
            "client_mode_enabled": True,
            "team_members_enabled": True,
            "price_per_month": 99.99,
            "is_active": True,
            "is_public": True,
        },
    ]
    with transaction.atomic():
        for data in plans:
            Plan.objects.update_or_create(slug=data["slug"], defaults=data)
