import uuid
from django.db import transaction

from assets.models.core import Asset
from assets.models.equity import EquityAsset, Exchange
from assets.models.core import AssetType
from fx.models.fx import FXCurrency
from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER


class EquitySeederService:
    """
    Rebuilds the ENTIRE equity universe using a snapshot strategy.

    Behavior:
    - Creates a brand new snapshot_id
    - Inserts ALL active equities from provider
    - DOES NOT update existing rows
    - DOES NOT delete old rows
    - Snapshot swap handled separately
    """

    @transaction.atomic
    def run(self) -> uuid.UUID:
        snapshot_id = uuid.UUID4()

        equity_type = AssetType.objects.get(slug="equity")

        rows = FMP_PROVIDER.get_actively_traded_equities()

        for row in rows:
            ticker = (row.get("symbol") or "").upper().strip()
            if not ticker:
                continue

            asset = Asset.objects.create(
                asset_type=equity_type
            )

            profile = FMP_PROVIDER.get_equity_profile(ticker)

            EquityAsset.objects.create(
                asset=asset,
                snapshot_id=snapshot_id,
                ticker=ticker,
                name=profile.get("companyName"),
                sector=profile.get("sector"),
                industry=profile.get("industry"),
                currency=FXCurrency.objects.filter(
                    code=profile.get("currency")
                ).first(),
                exchange=Exchange.objects.filter(
                    code=profile.get("exchangeShortName")
                ).first(),
                country=Country.objects.filter(
                    code=profile.get("country")
                ).first(),
            )

        return snapshot_id
