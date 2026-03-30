from django.db import transaction

from assets.models.equity import EquityAsset, Exchange
from assets.services.base import BaseAssetFactory
from fx.models.country import Country
from fx.models.fx import FXCurrency

from uuid import UUID

class EquityAssetFactory(BaseAssetFactory):
    asset_type_slug = "equity"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        snapshot_id: UUID,
        ticker: str,
        name: str,
        exchange: Exchange | None = None,
        country: Country | None = None,
        currency: FXCurrency | None = None,
        isin: str | None = None,
        cusip: str | None = None,
        cik: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
    ) -> EquityAsset:
        asset = cls._create_asset()

        return EquityAsset.objects.create(
            asset=asset,
            snapshot_id=snapshot_id,
            ticker=ticker,
            name=name,
            exchange=exchange,
            country=country,
            currency=currency,
            isin=isin,
            cusip=cusip,
            cik=cik,
            sector=sector,
            industry=industry,
        )
