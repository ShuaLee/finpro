import uuid
from django.db import transaction

from assets.services.commodity.commodity_factory import CommodityAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.providers.fmp.commodity.parsers import (
    parse_commodity_list_row,
)
from fx.models.fx import FXCurrency


class CommoditySeederService:

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
