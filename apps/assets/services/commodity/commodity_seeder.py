import uuid
from django.db import transaction

from accounts.models.holding import Holding
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

        # --------------------------------------------------
        # 1. Build fresh commodity universe
        # --------------------------------------------------
        rows = FMP_PROVIDER.get_commodities()

        new_assets_by_symbol = {}  # symbol -> Asset

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

            # CommodityAssetFactory MUST return the Asset
            new_assets_by_symbol[symbol] = commodity.asset

        # --------------------------------------------------
        # 2. Reconcile holdings (asset-backed only)
        # --------------------------------------------------
        holdings = Holding.objects.select_for_update().filter(
            source=Holding.SOURCE_ASSET,
        )

        for holding in holdings:
            symbol = holding.original_ticker

            if not symbol:
                # Defensive: no symbol = cannot relink
                holding.source = Holding.SOURCE_CUSTOM
                holding.custom_reason = Holding.CUSTOM_REASON_MARKET
                holding.asset = None
                holding.save(update_fields=[
                             "source", "custom_reason", "asset"])
                continue

            new_asset = new_assets_by_symbol.get(symbol)

            if new_asset:
                if holding.asset_id != new_asset.id:
                    holding.asset = new_asset
                    holding.save(update_fields=["asset"])
            else:
                # Commodity no longer active
                holding.source = Holding.SOURCE_CUSTOM
                holding.custom_reason = Holding.CUSTOM_REASON_MARKET
                holding.asset = None
                holding.save(update_fields=[
                             "source", "custom_reason", "asset"])

        return snapshot_id
