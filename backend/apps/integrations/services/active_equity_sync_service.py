from django.db import transaction

from apps.integrations.models import ActiveEquityListing
from apps.integrations.providers.fmp import FMP_PROVIDER


class ActiveEquitySyncService:
    @staticmethod
    def get_queryset(*, provider: str = "fmp"):
        return ActiveEquityListing.objects.filter(provider=provider)

    @staticmethod
    @transaction.atomic
    def refresh_from_fmp() -> dict:
        rows = FMP_PROVIDER.get_actively_traded_rows()

        ActiveEquityListing.objects.filter(provider="fmp").delete()
        ActiveEquityListing.objects.bulk_create(
            [
                ActiveEquityListing(
                    provider="fmp",
                    symbol=row["symbol"],
                    name=row["name"],
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
