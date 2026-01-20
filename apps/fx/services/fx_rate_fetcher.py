from decimal import Decimal

from django.db import transaction

from fx.models.fx import FXCurrency, FXRate
from external_data.providers.fmp.fx.fetchers import fetch_fx_quote
from external_data.exceptions import ExternalDataEmptyResult


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

        if len(symbol) < 6:
            raise ValueError("FX symbol must be at least 6 characters (e.g. EURUSD)")

        base = symbol[:3]
        quote = symbol[3:]

        data = fetch_fx_quote(symbol)

        rate_value = data.get("rate")
        if rate_value is None:
            raise ExternalDataEmptyResult(f"No rate returned for {symbol}")

        from_currency, _ = FXCurrency.objects.get_or_create(
            code=base,
            defaults={"name": base},
        )

        to_currency, _ = FXCurrency.objects.get_or_create(
            code=quote,
            defaults={"name": quote},
        )

        fx_rate, _ = FXRate.objects.update_or_create(
            from_currency=from_currency,
            to_currency=to_currency,
            defaults={
                "rate": Decimal(str(rate_value)),
            },
        )

        return fx_rate
