import uuid
from django.db import transaction

from assets.models.core import Asset, AssetType
from assets.models.commodity.precious_metal import PreciousMetalAsset
from assets.services.commodity.commodity_factory import CommodityAssetFactory
from assets.services.commodity.constants import PRECIOUS_METAL_COMMODITY_MAP
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.providers.fmp.commodity.parsers import parse_commodity_list_row
from fx.models.fx import FXCurrency


class CommoditySeederService:
    """
    Rebuilds the ENTIRE commodity universe using a snapshot strategy.

    Responsibilities:
    - Build commodity assets
    - Derive precious metals
    - NOTHING ELSE
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        # ==================================================
        # 1️⃣ Build commodity universe
        # ==================================================
        rows = FMP_PROVIDER.get_commodities()

        commodity_assets_by_symbol = {}

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
        # 2️⃣ Rebuild precious metals (derived assets)
        # ==================================================
        pm_asset_type = AssetType.objects.get(slug="precious-metal")

        # IMPORTANT: delete derived rows first
        PreciousMetalAsset.objects.all().delete()
        Asset.objects.filter(asset_type=pm_asset_type).delete()

        for metal, commodity_symbol in PRECIOUS_METAL_COMMODITY_MAP.items():
            commodity_asset = commodity_assets_by_symbol.get(commodity_symbol)
            if not commodity_asset:
                continue

            asset = Asset.objects.create(
                asset_type=pm_asset_type,
            )

            PreciousMetalAsset.objects.create(
                asset=asset,
                metal=metal,
                commodity=commodity_asset.commodity,
            )

        return snapshot_id
