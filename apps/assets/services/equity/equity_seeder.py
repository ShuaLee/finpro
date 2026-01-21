import uuid
from django.db import transaction

from accounts.models.holding import Holding
from assets.models.core import Asset
from assets.services.equity.equity_factory import EquityAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER


class EquitySeederService:
    """
    Rebuilds the ENTIRE equity universe using a snapshot strategy.

    Holding reconciliation rules:
    - source=asset + ticker exists → relink
    - source=asset + ticker missing → become custom
    - source=custom → NEVER auto-relink
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        # --------------------------------------------------
        # 1. Rebuild equity universe
        # --------------------------------------------------
        rows = FMP_PROVIDER.get_actively_traded_equities()

        new_assets_by_ticker: dict[str, Asset] = {}

        for row in rows:
            ticker = (row.get("symbol") or "").upper().strip()
            name = (row.get("name") or "").strip()

            if not ticker:
                continue

            asset = EquityAssetFactory.create(
                snapshot_id=snapshot_id,
                ticker=ticker,
                name=name,
            )

            # EquityAssetFactory.create MUST return the Asset
            new_assets_by_ticker[ticker] = asset

        # --------------------------------------------------
        # 2. Reconcile holdings (ONLY asset-backed)
        # --------------------------------------------------
        holdings = Holding.objects.select_for_update().filter(
            source=Holding.SOURCE_ASSET,
        )

        for holding in holdings:
            ticker = holding.original_ticker

            if not ticker:
                holding.source = Holding.SOURCE_CUSTOM
                holding.custom_reason = Holding.CUSTOM_REASON_MARKET
                holding.asset = None
                holding.save(update_fields=[
                             "source", "custom_reason", "asset"])
                continue

            new_asset = new_assets_by_ticker.get(ticker)

            if new_asset:
                if holding.asset_id != new_asset.asset_id:
                    holding.asset = new_asset.asset
                    holding.save(update_fields=["asset"])
            else:
                holding.source = Holding.SOURCE_CUSTOM
                holding.custom_reason = Holding.CUSTOM_REASON_MARKET
                holding.asset = None
                holding.save(update_fields=[
                             "source", "custom_reason", "asset"])

        return snapshot_id
