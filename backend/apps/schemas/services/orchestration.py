from __future__ import annotations

from collections.abc import Iterable

from schemas.services.engine import SchemaEngine


class SchemaOrchestrationService:
    """
    Single entrypoint for recomputation events.
    """

    @staticmethod
    def _recompute_holdings(holdings: Iterable):
        for holding in holdings:
            account = holding.account
            schema = getattr(account, "active_schema", None)
            if not schema:
                continue

            engine = SchemaEngine.for_account(account)
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
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        ).prefetch_related("holdings")

        all_holdings = []
        for account in accounts:
            all_holdings.extend(account.holdings.all())

        SchemaOrchestrationService._recompute_holdings(all_holdings)
