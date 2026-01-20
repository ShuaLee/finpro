from schemas.services.schema_manager import SchemaManager


class SCVRefreshService:
    """
    Central recomputation orchestrator.

    Any domain mutation that *might* affect SCVs MUST
    route through this service.

    This guarantees:
        ✔ Deterministic updates
        ✔ No signals
        ✔ One recomputation path
        ✔ Easy debugging
    """

    # ==========================================================
    # HOLDING MUTATIONS
    # ==========================================================
    @staticmethod
    def holding_changed(holding):
        account = holding.account
        schema = account.active_schema

        if not schema:
            return

        SchemaManager.for_account(account).sync_for_holding(holding)

    # ==========================================================
    # ASSET MUTATIONS (PRICE, METADATA, SUB-ASSET)
    # ==========================================================
    @staticmethod
    def asset_changed(asset):
        """
        Called when:
            - AssetPrice updated
            - EquityAsset updated
            - CryptoAsset updated
            - Asset.currency changed
        """
        holdings = (
            asset.holdings
            .select_related("account")
            .all()
        )

        for holding in holdings:
            SCVRefreshService.holding_changed(holding)

    # ==========================================================
    # FX MUTATIONS
    # ==========================================================
    @staticmethod
    def fx_changed(currency):
        """
        Recompute all holdings priced in this currency.
        """
        holdings = (
            currency.equities
            .prefetch_related("asset__holdings__account")
            .values_list("asset__holdings", flat=True)
        )

        for holding in holdings:
            SCVRefreshService.holding_changed(holding)

    # ==========================================================
    # SCHEMA / COLUMN MUTATIONS
    # ==========================================================
    @staticmethod
    def schema_changed(schema):
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            manager = SchemaManager.for_account(account)
            for holding in account.holdings.all():
                manager.sync_for_holding(holding)
