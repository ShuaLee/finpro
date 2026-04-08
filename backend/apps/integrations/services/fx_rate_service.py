from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.integrations.models import FXRateCache
from apps.integrations.providers.fmp import FMP_PROVIDER


class FXRateService:
    @staticmethod
    def build_pair_symbol(*, base_currency: str, quote_currency: str) -> str:
        return f"{(base_currency or '').strip().upper()}{(quote_currency or '').strip().upper()}"

    @staticmethod
    def is_fresh(*, cache_row: FXRateCache | None) -> bool:
        if cache_row is None or cache_row.as_of is None:
            return False
        ttl_seconds = getattr(settings, "FX_RATE_CACHE_TTL_SECONDS", 3600)
        return cache_row.as_of >= timezone.now() - timedelta(seconds=ttl_seconds)

    @staticmethod
    def get_rate(
        *,
        base_currency: str | None,
        quote_currency: str | None,
        force_refresh: bool = False,
    ) -> Decimal:
        base = (base_currency or "").strip().upper()
        quote = (quote_currency or "").strip().upper()

        if not base or not quote or base == quote:
            return Decimal("1")

        cache_row = FXRateCache.objects.filter(
            provider="fmp",
            base_currency=base,
            quote_currency=quote,
        ).first()
        if not force_refresh and FXRateService.is_fresh(cache_row=cache_row):
            return cache_row.rate

        try:
            quote_snapshot = FMP_PROVIDER.get_quote(FXRateService.build_pair_symbol(base_currency=base, quote_currency=quote))
            if quote_snapshot.price is None:
                raise ValueError("Missing FX quote price.")
            cache_row, _ = FXRateCache.objects.update_or_create(
                provider="fmp",
                base_currency=base,
                quote_currency=quote,
                defaults={
                    "pair_symbol": quote_snapshot.symbol,
                    "rate": quote_snapshot.price,
                    "source_payload": {
                        "symbol": quote_snapshot.symbol,
                        "price": str(quote_snapshot.price),
                        "change": str(quote_snapshot.change) if quote_snapshot.change is not None else None,
                        "volume": quote_snapshot.volume,
                        "source": quote_snapshot.source,
                    },
                },
            )
            return cache_row.rate
        except Exception:
            if cache_row is not None:
                return cache_row.rate
            raise
