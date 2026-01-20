from django.db import transaction

from external_data.providers.fmp.client import FMP_PROVIDER
from fx.models.fx import FXCurrency
from fx.models.country import Country
from assets.models.equity.exchange import Exchange
from schemas.services.scv_refresh_service import SCVRefreshService


class EquityProfileSyncService:
    """
    Syncs profile metadata for a single EquityAsset.
    """
    @transaction.atomic
    def sync(self, equity):
        data = FMP_PROVIDER.get_equity_identity(equity.ticker)

        profile = data.profile
        identifiers = data.identifiers

        updated_fields: list[str] = []

        def apply(field: str, value):
            if value is not None and getattr(equity, field) != value:
                setattr(equity, field, value)
                updated_fields.append(field)

        # -------------------------
        # Identity (CRITICAL)
        # -------------------------
        apply("isin", identifiers.isin)
        apply("cusip", identifiers.cusip)
        apply("cik", identifiers.cik)

        # -------------------------
        # Scalar fields
        # -------------------------
        apply("name", profile.get("name"))
        apply("sector", profile.get("sector"))
        apply("industry", profile.get("industry"))
        apply("description", profile.get("description"))
        apply("image_url", profile.get("image_url"))
        apply("website", profile.get("website"))
        apply("ipo_date", profile.get("ipo_date"))
        apply("market_cap", profile.get("market_cap"))
        apply("beta", profile.get("beta"))
        apply("last_dividend", profile.get("last_dividend"))

        # -------------------------
        # Flags
        # -------------------------
        for flag in ("is_actively_trading", "is_adr", "is_etf", "is_fund"):
            if flag in profile:
                apply(flag, bool(profile.get(flag)))

        # -------------------------
        # Country
        # -------------------------
        country_code = profile.get("country")
        if country_code:
            country = Country.objects.filter(code=country_code).first()
            if country and equity.country_id != country.pk:
                equity.country = country
                updated_fields.append("country")

        # -------------------------
        # Currency
        # -------------------------
        currency_code = profile.get("currency")
        if currency_code:
            fx = FXCurrency.objects.filter(code=currency_code).first()
            if fx and equity.currency_id != fx.pk:
                equity.currency = fx
                updated_fields.append("currency")

        # -------------------------
        # Exchange
        # -------------------------
        exchange_code = profile.get("exchange")
        if exchange_code:
            exchange = Exchange.objects.filter(code=exchange_code).first()
            if exchange and equity.exchange_id != exchange.pk:
                equity.exchange = exchange
                updated_fields.append("exchange")

        # -------------------------
        # Persist
        # -------------------------
        if updated_fields:
            equity.save(update_fields=updated_fields)

            SCVRefreshService.asset_changed(equity.asset)

        return {
            "ticker": equity.ticker,
            "updated_fields": updated_fields,
        }
