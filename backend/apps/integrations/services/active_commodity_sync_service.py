from django.db import transaction

from apps.integrations.models import ActiveCommodityListing
from apps.integrations.providers.fmp import FMP_PROVIDER


class ActiveCommoditySyncService:
    @staticmethod
    def get_queryset(*, provider: str = "fmp"):
        return ActiveCommodityListing.objects.filter(provider=provider)

    @staticmethod
    @transaction.atomic
    def refresh_from_fmp() -> dict:
        rows = FMP_PROVIDER.get_commodity_rows()

        ActiveCommodityListing.objects.filter(provider="fmp").delete()
        ActiveCommodityListing.objects.bulk_create(
            [
                ActiveCommodityListing(
                    provider="fmp",
                    symbol=row["symbol"],
                    name=row["name"],
                    exchange=row["exchange"],
                    trade_month=row["trade_month"],
                    currency=row["currency"],
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
