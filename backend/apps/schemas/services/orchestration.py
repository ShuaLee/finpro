from __future__ import annotations

from collections.abc import Iterable

from accounts.models import Holding
from schemas.services.engine import SchemaEngine


class SchemaOrchestrationService:
    """
    Single entrypoint for recomputation events.
    """

    @staticmethod
    def _recompute_holdings(holdings: Iterable):
        for holding in holdings:
            schema = getattr(holding, "active_schema", None)
            if not schema:
                continue

            engine = SchemaEngine(schema)
            engine.sync_scvs_for_holding(holding)

    @staticmethod
    def holding_changed(holding):
        SchemaOrchestrationService._recompute_holdings([holding])

    @staticmethod
    def holdings_changed(holdings: Iterable):
        SchemaOrchestrationService._recompute_holdings(holdings)

    @staticmethod
    def asset_changed(asset):
        holdings = asset.holdings.select_related("account").all()
        SchemaOrchestrationService._recompute_holdings(holdings)

    @staticmethod
    def fx_changed(holdings: Iterable):
        SchemaOrchestrationService._recompute_holdings(holdings)

    @staticmethod
    def schema_changed(schema):
        holdings = Holding.objects.filter(account__portfolio=schema.portfolio).select_related(
            "account",
            "asset",
            "asset__asset_type",
        )
        if schema.asset_type_id:
            holdings = holdings.filter(asset__asset_type=schema.asset_type)

        all_holdings = [
            holding
            for holding in holdings
            if holding.active_schema and holding.active_schema.id == schema.id
        ]

        SchemaOrchestrationService._recompute_holdings(all_holdings)
