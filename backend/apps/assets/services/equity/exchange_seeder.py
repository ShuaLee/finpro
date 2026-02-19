from django.db import transaction

from assets.models.equity import Exchange
from fx.models.country import Country
from external_data.providers.fmp.client import FMP_PROVIDER


class ExchangeSeederService:
    """
    Rebuilds the exchange reference table from provider data.
    Safe to truncate and rebuild.
    """

    @classmethod
    @transaction.atomic
    def run(cls) -> None:
        Exchange.objects.all().delete()

        rows = FMP_PROVIDER.get_available_exchanges()

        for row in rows:
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()

            if not code or not name:
                continue

            country = None
            if country_code := row.get("country_code"):
                country = Country.objects.filter(
                    code=country_code.upper()
                ).first()

            Exchange.objects.create(
                code=code,
                name=name,
                country=country,
                symbol_suffix=row.get("symbol_suffix"),
                delay=row.get("delay"),
            )
