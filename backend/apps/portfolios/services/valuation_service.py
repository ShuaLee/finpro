from __future__ import annotations

from decimal import Decimal, InvalidOperation

from assets.models import Asset, AssetPrice, CommodityAsset, CryptoAsset, EquityAsset
from fx.models import FXRate
from portfolios.models import PortfolioDenomination, PortfolioValuationSnapshot
from schemas.models import SchemaColumnValue


class PortfolioValuationService:
    DEFAULT_DENOMINATIONS = [
        {
            "key": "profile_currency",
            "label": "Profile Currency",
            "kind": PortfolioDenomination.Kind.PROFILE_CURRENCY,
            "display_order": 1,
            "is_system": True,
            "unit_label": None,
            "reference_code": None,
        },
        {
            "key": "btc_units",
            "label": "Bitcoin",
            "kind": PortfolioDenomination.Kind.ASSET_UNITS,
            "display_order": 2,
            "is_system": True,
            "unit_label": "BTC",
            "reference_code": "BTC",
        },
        {
            "key": "gold_oz",
            "label": "Gold Ounces",
            "kind": PortfolioDenomination.Kind.ASSET_UNITS,
            "display_order": 3,
            "is_system": True,
            "unit_label": "oz",
            "reference_code": "GCUSD",
        },
        {
            "key": "silver_oz",
            "label": "Silver Ounces",
            "kind": PortfolioDenomination.Kind.ASSET_UNITS,
            "display_order": 4,
            "is_system": True,
            "unit_label": "oz",
            "reference_code": "SIUSD",
        },
        {
            "key": "aapl_shares",
            "label": "Apple Shares",
            "kind": PortfolioDenomination.Kind.ASSET_UNITS,
            "display_order": 5,
            "is_system": True,
            "unit_label": "shares",
            "reference_code": "AAPL",
        },
    ]

    @staticmethod
    def _to_decimal(raw) -> Decimal:
        if raw in (None, ""):
            return Decimal("0")
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    @staticmethod
    def _fx_rate(*, from_code: str, to_code: str) -> Decimal | None:
        if from_code == to_code:
            return Decimal("1")

        direct = FXRate.objects.filter(
            from_currency__code=from_code,
            to_currency__code=to_code,
        ).first()
        if direct:
            return Decimal(str(direct.rate))

        inverse = FXRate.objects.filter(
            from_currency__code=to_code,
            to_currency__code=from_code,
        ).first()
        if inverse and inverse.rate:
            try:
                return Decimal("1") / Decimal(str(inverse.rate))
            except (InvalidOperation, ZeroDivisionError):
                return None
        return None

    @staticmethod
    def _asset_currency_code(asset: Asset) -> str | None:
        if hasattr(asset, "custom"):
            return getattr(getattr(asset.custom, "currency", None), "code", None)

        ext = asset.extension
        if not ext:
            return None
        currency = getattr(ext, "currency", None)
        return getattr(currency, "code", None)

    @staticmethod
    def _resolve_asset_by_reference(*, reference_code: str) -> Asset | None:
        code = (reference_code or "").strip().upper()
        if not code:
            return None

        equity = EquityAsset.objects.filter(ticker__iexact=code).select_related("asset").first()
        if equity:
            return equity.asset

        crypto = CryptoAsset.objects.filter(base_symbol__iexact=code).select_related("asset").first()
        if crypto:
            return crypto.asset

        commodity = CommodityAsset.objects.filter(symbol__iexact=code).select_related("asset").first()
        if commodity:
            return commodity.asset

        if code == "XAU":
            commodity = CommodityAsset.objects.filter(symbol__iexact="GCUSD").select_related("asset").first()
            if commodity:
                return commodity.asset

        if code == "XAG":
            commodity = CommodityAsset.objects.filter(symbol__iexact="SIUSD").select_related("asset").first()
            if commodity:
                return commodity.asset

        return None

    @staticmethod
    def ensure_default_denominations(*, portfolio):
        for template in PortfolioValuationService.DEFAULT_DENOMINATIONS:
            defaults = {
                "label": template["label"],
                "kind": template["kind"],
                "display_order": template["display_order"],
                "is_system": template["is_system"],
                "is_active": True,
                "unit_label": template["unit_label"],
                "reference_code": template["reference_code"],
            }
            denom, _ = PortfolioDenomination.objects.get_or_create(
                portfolio=portfolio,
                key=template["key"],
                defaults=defaults,
            )
            if denom.kind == PortfolioDenomination.Kind.ASSET_UNITS and not denom.asset_id and denom.reference_code:
                asset = PortfolioValuationService._resolve_asset_by_reference(reference_code=denom.reference_code)
                if asset:
                    denom.asset = asset
                    denom.save(update_fields=["asset", "updated_at"])

    @staticmethod
    def compute_total_value(*, portfolio, identifier: str = "current_value") -> Decimal:
        values = SchemaColumnValue.objects.filter(
            holding__account__portfolio=portfolio,
            column__identifier=identifier,
        ).values_list("value", flat=True)

        total = Decimal("0")
        for value in values:
            total += PortfolioValuationService._to_decimal(value)
        return total.quantize(Decimal("0.01"))

    @staticmethod
    def _denomination_value(*, portfolio, total_value: Decimal, denomination: PortfolioDenomination):
        profile_currency = portfolio.profile.currency.code

        if denomination.kind == PortfolioDenomination.Kind.PROFILE_CURRENCY:
            return {
                "key": denomination.key,
                "label": denomination.label,
                "kind": denomination.kind,
                "value": str(total_value),
                "unit": profile_currency,
                "is_available": True,
            }

        if denomination.kind == PortfolioDenomination.Kind.CURRENCY:
            if not denomination.currency_id:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": None,
                    "is_available": False,
                    "reason": "currency_not_configured",
                }
            rate = PortfolioValuationService._fx_rate(
                from_code=profile_currency,
                to_code=denomination.currency.code,
            )
            if not rate:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.currency.code,
                    "is_available": False,
                    "reason": "fx_rate_missing",
                }
            converted = (total_value * rate).quantize(Decimal("0.01"))
            return {
                "key": denomination.key,
                "label": denomination.label,
                "kind": denomination.kind,
                "value": str(converted),
                "unit": denomination.currency.code,
                "is_available": True,
            }

        if denomination.kind == PortfolioDenomination.Kind.ASSET_UNITS:
            asset = denomination.asset
            if not asset and denomination.reference_code:
                asset = PortfolioValuationService._resolve_asset_by_reference(reference_code=denomination.reference_code)
                if asset:
                    denomination.asset = asset
                    denomination.save(update_fields=["asset", "updated_at"])

            if not asset:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.unit_label,
                    "is_available": False,
                    "reason": "asset_not_found",
                }

            price_row = AssetPrice.objects.filter(asset=asset).first()
            if not price_row or not price_row.price:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.unit_label,
                    "is_available": False,
                    "reason": "asset_price_missing",
                }

            asset_currency = PortfolioValuationService._asset_currency_code(asset)
            if not asset_currency:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.unit_label,
                    "is_available": False,
                    "reason": "asset_currency_missing",
                }

            fx_rate = PortfolioValuationService._fx_rate(
                from_code=asset_currency,
                to_code=profile_currency,
            )
            if not fx_rate:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.unit_label,
                    "is_available": False,
                    "reason": "fx_rate_missing",
                }

            unit_price_profile = Decimal(str(price_row.price)) * fx_rate
            if unit_price_profile <= 0:
                return {
                    "key": denomination.key,
                    "label": denomination.label,
                    "kind": denomination.kind,
                    "value": None,
                    "unit": denomination.unit_label,
                    "is_available": False,
                    "reason": "asset_price_invalid",
                }

            units = (total_value / unit_price_profile).quantize(Decimal("0.000001"))
            return {
                "key": denomination.key,
                "label": denomination.label,
                "kind": denomination.kind,
                "value": str(units),
                "unit": denomination.unit_label,
                "is_available": True,
            }

        return {
            "key": denomination.key,
            "label": denomination.label,
            "kind": denomination.kind,
            "value": None,
            "unit": None,
            "is_available": False,
            "reason": "unsupported_kind",
        }

    @staticmethod
    def valuation_payload(*, portfolio, identifier: str = "current_value") -> dict:
        PortfolioValuationService.ensure_default_denominations(portfolio=portfolio)
        total = PortfolioValuationService.compute_total_value(portfolio=portfolio, identifier=identifier)

        denominations = []
        for denomination in portfolio.denominations.filter(is_active=True).order_by("display_order", "key"):
            denominations.append(
                PortfolioValuationService._denomination_value(
                    portfolio=portfolio,
                    total_value=total,
                    denomination=denomination,
                )
            )

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "profile_currency": portfolio.profile.currency.code,
            "base_value_identifier": identifier,
            "total_value": str(total),
            "denominations": denominations,
        }

    @staticmethod
    def capture_snapshot(*, portfolio, identifier: str = "current_value"):
        payload = PortfolioValuationService.valuation_payload(
            portfolio=portfolio,
            identifier=identifier,
        )
        snapshot = PortfolioValuationSnapshot.objects.create(
            portfolio=portfolio,
            base_value_identifier=identifier,
            profile_currency_code=portfolio.profile.currency.code,
            total_value=Decimal(payload["total_value"]),
            denominations=payload["denominations"],
        )
        return snapshot
