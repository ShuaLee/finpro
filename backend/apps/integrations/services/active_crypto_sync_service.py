from django.db import transaction

from apps.integrations.models import ActiveCryptoListing
from apps.integrations.providers.fmp import FMP_PROVIDER


class ActiveCryptoSyncService:
    @staticmethod
    def get_queryset(*, provider: str = "fmp"):
        return ActiveCryptoListing.objects.filter(provider=provider)

    @staticmethod
    @transaction.atomic
    def refresh_from_fmp() -> dict:
        rows = FMP_PROVIDER.get_cryptocurrency_rows()

        ActiveCryptoListing.objects.filter(provider="fmp").delete()
        ActiveCryptoListing.objects.bulk_create(
            [
                ActiveCryptoListing(
                    provider="fmp",
                    symbol=row["symbol"],
                    name=row["name"],
                    base_symbol=row["base_symbol"],
                    quote_currency=row["quote_currency"],
                    source_payload=row,
                )
                for row in rows
            ],
            batch_size=5000,
        )

        return {
            "provider": "fmp",
            "row_count": len(rows),
        }
