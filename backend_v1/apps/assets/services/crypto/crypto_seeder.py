import uuid
from django.db import transaction

from assets.services.crypto.crypto_factory import CryptoAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.providers.fmp.crypto.parsers import parse_crypto_list_row
from fx.models.fx import FXCurrency


class CryptoSeederService:
    """
    Rebuilds the ENTIRE crypto universe using a snapshot strategy.

    Responsibilities:
    - Build a fresh snapshot of CryptoAsset + Asset rows
    - NOTHING ELSE
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        rows = FMP_PROVIDER.get_cryptocurrencies()

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

            CryptoAssetFactory.create(
                snapshot_id=snapshot_id,
                base_symbol=base_symbol,
                pair_symbol=pair_symbol,
                name=parsed.get("name"),
                currency=currency,
                circulating_supply=parsed.get("circulating_supply"),
                total_supply=parsed.get("total_supply"),
                ico_date=parsed.get("ico_date"),
            )

        return snapshot_id
