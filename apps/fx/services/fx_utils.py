from django.core.exceptions import ValidationError

from fx.models.country import Country
from fx.models.fx import FXCurrency


# =====================================================
# Currency
# =====================================================

def resolve_fx_currency(code: str | None) -> FXCurrency | None:
    """
    Resolve ISO-4217 currency code to FXCurrency.

    - Case-insensitive
    - Returns None if not found
    - NEVER creates records
    """
    if not code:
        return None

    return FXCurrency.objects.filter(code=code.upper().strip()).first()


def validate_fx_currency(code: str) -> FXCurrency:
    """
    Strict currency validator.

    Raises ValidationError if the currency does not exist.
    """
    if not code:
        raise ValidationError("Currency code is required.")

    currency = resolve_fx_currency(code)
    if not currency:
        raise ValidationError(f"Unsupported currency code: '{code}'")

    return currency


# =====================================================
# Country
# =====================================================

def resolve_country(code: str | None) -> Country | None:
    """
    Resolve ISO-3166 alpha-2 country code.

    - Case-insensitive
    - Returns None if not found
    - NEVER creates records
    """
    if not code:
        return None

    return Country.objects.filter(code=code.upper().strip()).first()


def validate_country(code: str) -> Country:
    """
    Strict country validator.

    Raises ValidationError if the country does not exist.
    """
    if not code:
        raise ValidationError("Country code is required.")

    country = resolve_country(code)
    if not country:
        raise ValidationError(f"Unsupported country code: '{code}'")

    return country
