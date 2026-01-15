import uuid
from django.db import transaction

from assets.services.equity.equity_factory import EquityAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER


class EquitySeederService:
    """
    Rebuilds the ENTIRE equity universe using a snapshot strategy.

    - Creates a brand new snapshot_id
    - Inserts ALL active equities (ticker + name only)
    - Does NOT delete or modify existing data
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.uuid4()

        rows = FMP_PROVIDER.get_actively_traded_equities()

        for row in rows:
            ticker = (row.get("symbol") or "").upper().strip()
            name = (row.get("name") or "").strip()

            if not ticker:
                continue

            EquityAssetFactory.create(
                snapshot_id=snapshot_id,
                ticker=ticker,
                name=name,
            )

        return snapshot_id
