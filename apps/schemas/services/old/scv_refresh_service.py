from typing import Iterable

from schemas.services.schema_manager import SchemaManager


class SCVRefreshService:
    """
    Central recomputation orchestrator.

    ❗ This is the ONLY entry point for recomputing SchemaColumnValues (SCVs).

    Responsibilities:
        - Determine WHICH holdings must be recomputed
        - Invoke SchemaManager deterministically
        - Enforce a single recomputation pathway

    Non-responsibilities:
        ❌ Compute values
        ❌ Resolve formula dependencies
        ❌ Evaluate formulas
        ❌ Create schema columns
        ❌ Attach constraints
    """

    # ==========================================================
    # INTERNAL CORE
    # ==========================================================
    @staticmethod
    def _recompute_holdings(holdings: Iterable):
        """
        Recompute SCVs for the given holdings.

        This is the ONLY place where SchemaManager.sync_scvs_for_holding
        may be called.
        """
        for holding in holdings:
            account = holding.account
            schema = getattr(account, "active_schema", None)

            if not schema:
                continue

            manager = SchemaManager.for_account(account)
            manager.sync_scvs_for_holding(holding)

    # ==========================================================
    # HOLDING-LEVEL EVENTS
    # ==========================================================
    @staticmethod
    def holding_changed(holding):
        """
        Called when a single holding changes, including:
            - quantity
            - cost basis
            - manual field edits
            - holding metadata changes
        """
        SCVRefreshService._recompute_holdings([holding])

    # ==========================================================
    # ASSET-LEVEL EVENTS
    # ==========================================================
    @staticmethod
    def asset_changed(asset):
        """
        Called when an asset changes, including:
            - price updates
            - metadata changes
            - asset-level recalculations
        """
        holdings = (
            asset.holdings
            .select_related("account")
            .all()
        )

        SCVRefreshService._recompute_holdings(holdings)

    # ==========================================================
    # FX / CURRENCY EVENTS
    # ==========================================================
    @staticmethod
    def fx_changed(holdings: Iterable):
        """
        Called when an FX rate changes.

        Caller is responsible for supplying the affected holdings.
        """
        SCVRefreshService._recompute_holdings(holdings)

    # ==========================================================
    # SCHEMA-LEVEL EVENTS
    # ==========================================================
    @staticmethod
    def schema_changed(schema):
        """
        Called when the schema structure changes, including:
            - column added
            - column deleted
            - formula attached or detached
            - constraints modified

        Recomputes ALL holdings for accounts using this schema.
        """
        accounts = (
            schema.portfolio.accounts.filter(
                account_type=schema.account_type).prefetch_related("holdings")
        )

        holdings = []
        for account in accounts:
            holdings.extend(account.holdings.all())

        SCVRefreshService._recompute_holdings(holdings)
