from schemas.services.schema_manager import SchemaManager


class SCVRefreshService:
    """
    Central recomputation orchestrator.

    Any domain mutation that *might* affect SchemaColumnValues (SCVs)
    MUST route through this service.

    Guarantees:
        ✔ Deterministic updates
        ✔ No signals
        ✔ Single recomputation authority
        ✔ Easy debugging
    """

    # ==========================================================
    # INTERNAL CORE
    # ==========================================================
    @staticmethod
    def _recompute_holdings(holdings):
        """
        Recompute SCVs for a collection of holdings.

        This is the ONLY place where SchemaManager.sync_for_holding
        is called.
        """
        for holding in holdings:
            account = holding.account
            schema = account.active_schema

            if not schema:
                continue

            manager = SchemaManager.for_account(account)
            manager.sync_for_holding(holding)

    # ==========================================================
    # HOLDING MUTATIONS
    # ==========================================================
    @staticmethod
    def holding_changed(holding):
        """
        Called when a single holding changes:
            - quantity
            - cost basis
            - manual field edits
        """
        SCVRefreshService._recompute_holdings([holding])

    # ==========================================================
    # ASSET MUTATIONS (PRICE, METADATA, SUB-ASSET)
    # ==========================================================
    @staticmethod
    def asset_changed(asset):
        """
        Called when:
            - AssetPrice updated
            - Equity / Crypto / Commodity metadata updated
            - Asset currency changed
        """
        holdings = (
            asset.holdings
            .select_related("account")
            .all()
        )

        SCVRefreshService._recompute_holdings(holdings)

    # ==========================================================
    # FX MUTATIONS
    # ==========================================================
    @staticmethod
    def fx_changed(currency):
        """
        Recompute all holdings whose asset pricing depends on this currency.
        """
        holdings = (
            currency.equities
            .prefetch_related("asset__holdings__account")
            .values_list("asset__holdings", flat=True)
        )

        SCVRefreshService._recompute_holdings(holdings)

    # ==========================================================
    # SCHEMA / COLUMN MUTATIONS
    # ==========================================================
    @staticmethod
    def schema_changed(schema):
        """
        Called when:
            - SchemaColumn added / deleted
            - Formula attached / detached
            - Constraints changed
        """
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        ).prefetch_related("holdings")

        holdings = []
        for account in accounts:
            holdings.extend(account.holdings.all())

        SCVRefreshService._recompute_holdings(holdings)
