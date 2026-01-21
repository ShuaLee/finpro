import uuid
from django.db import transaction

from accounts.models.holding import Holding
from assets.services.crypto.crypto_factory import CryptoAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.providers.fmp.crypto.parsers import parse_crypto_list_row
from fx.models.fx import FXCurrency


class CryptoSeederService:

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        # --------------------------------------------------
        # 1. Build fresh crypto universe
        # --------------------------------------------------
        rows = FMP_PROVIDER.get_cryptocurrencies()

        new_assets_by_symbol = {}  # base_symbol -> Asset

        for row in rows:
            parsed = parse_crypto_list_row(row)

            pair_symbol = parsed.get("pair_symbol")
            base_symbol = parsed.get("base_symbol")
            currency_code = parsed.get("currency_code")

            if not pair_symbol or not base_symbol or not currency_code:
                continue

            currency = FXCurrency.objects.filter(code=currency_code).first()
            if not currency:
                continue

            crypto = CryptoAssetFactory.create(
                snapshot_id=snapshot_id,
                base_symbol=base_symbol,
                pair_symbol=pair_symbol,
                name=parsed.get("name"),
                currency=currency,
                circulating_supply=parsed.get("circulating_supply"),
                total_supply=parsed.get("total_supply"),
                ico_date=parsed.get("ico_date"),
            )

            # CryptoAssetFactory MUST return the Asset
            new_assets_by_symbol[base_symbol] = crypto.asset

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
                # Asset disappeared from active universe
                holding.source = Holding.SOURCE_CUSTOM
                holding.custom_reason = Holding.CUSTOM_REASON_MARKET
                holding.asset = None
                holding.save(update_fields=[
                             "source", "custom_reason", "asset"])

        return snapshot_id
