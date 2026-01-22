import uuid
from django.db import transaction

from accounts.models.holding import Holding
from assets.models.core import Asset, AssetType
from assets.models.commodity.precious_metal import PreciousMetalAsset
from assets.services.commodity.commodity_factory import CommodityAssetFactory
from assets.services.commodity.constants import (
    PRECIOUS_METAL_COMMODITY_MAP,
)
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.providers.fmp.commodity.parsers import (
    parse_commodity_list_row,
)
from fx.models.fx import FXCurrency


class CommoditySeederService:

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        # ==================================================
        # 1. Build fresh commodity universe
        # ==================================================
        rows = FMP_PROVIDER.get_commodities()

        commodity_assets_by_symbol: dict[str, Asset] = {}

        for row in rows:
            parsed = parse_commodity_list_row(row)

            symbol = parsed.get("symbol")
            currency_code = parsed.get("currency_code")

            if not symbol or not currency_code:
                continue

            currency = FXCurrency.objects.filter(code=currency_code).first()
            if not currency:
                continue

            commodity = CommodityAssetFactory.create(
                snapshot_id=snapshot_id,
                symbol=symbol,
                name=parsed.get("name"),
                currency=currency,
                exchange=parsed.get("exchange"),
                trade_month=parsed.get("trade_month"),
            )

            commodity_assets_by_symbol[symbol] = commodity.asset

        # ==================================================
        # 2. Derive precious metals from commodities
        # ==================================================

        # 🔥 IMPORTANT FIX:
        # Precious metals are derived assets and MUST be deleted
        # before recreating them, otherwise they PROTECT old commodities
        # and orphaned PM assets can accumulate.

        pm_asset_type = AssetType.objects.get(slug="precious-metal")

        # 1️⃣ Delete PM detail rows (if any)
        PreciousMetalAsset.objects.all().delete()

        # 2️⃣ Delete ALL precious-metal Assets (including orphans)
        Asset.objects.filter(asset_type=pm_asset_type).delete()

        precious_metal_assets_by_symbol: dict[str, Asset] = {}

        for metal, commodity_symbol in PRECIOUS_METAL_COMMODITY_MAP.items():
            commodity_asset = commodity_assets_by_symbol.get(commodity_symbol)
            if not commodity_asset:
                continue  # metal unavailable this snapshot

            asset = Asset.objects.create(
                asset_type=pm_asset_type,
            )

            PreciousMetalAsset.objects.create(
                asset=asset,
                metal=metal,
                commodity=commodity_asset.commodity,
            )

            # use metal name as the reconciliation key
            precious_metal_assets_by_symbol[metal.lower()] = asset

        # ==================================================
        # 3. Reconcile holdings (commodities + precious metals)
        # ==================================================
        holdings = Holding.objects.select_for_update().filter(
            source=Holding.SOURCE_ASSET,
        )

        for holding in holdings:
            symbol = holding.original_ticker

            if not symbol:
                self._fallback_to_custom(holding)
                continue

            # Try commodity first
            new_asset = commodity_assets_by_symbol.get(symbol)

            # Then precious metal
            if not new_asset:
                new_asset = precious_metal_assets_by_symbol.get(symbol.lower())

            if new_asset:
                if holding.asset_id != new_asset.id:
                    holding.asset = new_asset
                    holding.save(update_fields=["asset"])
            else:
                self._fallback_to_custom(holding)

        return snapshot_id

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    @staticmethod
    def _fallback_to_custom(holding: Holding):
        holding.source = Holding.SOURCE_CUSTOM
        holding.custom_reason = Holding.CUSTOM_REASON_MARKET
        holding.asset = None
        holding.save(update_fields=[
            "source",
            "custom_reason",
            "asset",
        ])
