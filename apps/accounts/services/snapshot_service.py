from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from accounts.models import HoldingSnapshot


class HoldingSnapshotService:
    @staticmethod
    @transaction.atomic
    def capture_holding(*, holding, as_of=None, source: str = "system"):
        as_of = as_of or timezone.now()
        price = None
        value = None
        if holding.asset_id and hasattr(holding.asset, "price") and holding.asset.price:
            price = holding.asset.price.price
            value = (price or Decimal("0")) * holding.quantity

        snapshot, _ = HoldingSnapshot.objects.update_or_create(
            holding=holding,
            as_of=as_of,
            defaults={
                "quantity": holding.quantity,
                "average_purchase_price": holding.average_purchase_price,
                "price": price,
                "value_profile_currency": value,
                "source": source,
            },
        )
        return snapshot

    @staticmethod
    @transaction.atomic
    def capture_account(*, account, as_of=None, source: str = "system"):
        snapshots = []
        for holding in account.holdings.select_related("asset", "asset__price").all():
            snapshots.append(
                HoldingSnapshotService.capture_holding(
                    holding=holding,
                    as_of=as_of,
                    source=source,
                )
            )
        return snapshots

