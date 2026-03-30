from rest_framework import serializers

from subscriptions.models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "name",
            "slug",
            "tier",
            "description",
            "max_stocks",
            "allow_crypto",
            "allow_metals",
            "max_portfolios",
            "max_accounts_total",
            "max_equity_accounts",
            "max_holdings_total",
            "max_stock_holdings",
            "max_crypto_holdings",
            "max_real_estate_holdings",
            "custom_assets_enabled",
            "custom_asset_types_enabled",
            "custom_schemas_enabled",
            "advanced_analytics_enabled",
            "allocations_enabled",
            "client_mode_enabled",
            "team_members_enabled",
            "price_per_month",
        ]
