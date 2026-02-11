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
    - Build commodity assets (snapshot-based)
    - NOTHING ELSE

    SnapshotCleanupService handles stale conversion.
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        rows = FMP_PROVIDER.get_commodities()

        for row in rows:
            parsed = parse_commodity_list_row(row)

            symbol = parsed.get("symbol")
            currency_code = parsed.get("currency_code")

            if not symbol or not currency_code:
                continue

            currency = FXCurrency.objects.filter(code=currency_code).first()
            if not currency:
                continue

            CommodityAssetFactory.create(
                snapshot_id=snapshot_id,
                symbol=symbol,
                name=parsed.get("name"),
                currency=currency,
                exchange=parsed.get("exchange"),
                trade_month=parsed.get("trade_month"),
            )

        return snapshot_id
