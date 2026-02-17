from decimal import Decimal

from django.db import transaction

from fx.models.fx import FXCurrency, FXRate
from external_data.exceptions import ExternalDataEmptyResult
from external_data.providers.fmp.client import FMP_PROVIDER


class FXRateFetcherService:
    """
    Fetch and persist a single FX rate from FMP.
    """

    @transaction.atomic
    def run(self, symbol: str) -> FXRate:
        """
        Example:
            symbol = "EURUSD"
        """
        symbol = symbol.strip().upper()

        if len(symbol) != 6:
            raise ValueError("FX symbol must be exactly 6 characters (e.g. EURUSD)")

        base = symbol[:3]
        quote = symbol[3:]

        quote_data = FMP_PROVIDER.get_fx_quote(base=base, quote=quote)
        rate_value = quote_data.rate
        if rate_value is None:
            raise ExternalDataEmptyResult(f"No rate returned for {symbol}")

        from_currency, _ = FXCurrency.objects.get_or_create(
            code=base,
            defaults={"name": base, "is_active": True},
        )
        if not from_currency.is_active:
            from_currency.is_active = True
            from_currency.save(update_fields=["is_active", "updated_at"])

        to_currency, _ = FXCurrency.objects.get_or_create(
            code=quote,
            defaults={"name": quote, "is_active": True},
        )
        if not to_currency.is_active:
            to_currency.is_active = True
            to_currency.save(update_fields=["is_active", "updated_at"])

        fx_rate, _ = FXRate.objects.update_or_create(
            from_currency=from_currency,
            to_currency=to_currency,
            defaults={
                "rate": Decimal(str(rate_value)),
            },
        )

        return fx_rate
