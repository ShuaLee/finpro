from django.core.exceptions import ValidationError

from fx.models.country import Country
from fx.models.fx import FXCurrency


def resolve_fx_currency(code: str | None) -> FXCurrency | None:
    """
    Universal currency resolver used by all data sync services.
    - Normalizes casing
    - Returns FXCurrency instance or None
    """
    if not code:
        return None

    code = code.upper().strip()
    return FXCurrency.objects.filter(code=code).first()

def validate_fx_currency(code: str) -> FXCurrency:
    """
    Strict validator for ISO 4217 currency codes.
    Uses resolve_fx_currency(), but raises ValidationError if not found.
    """
    if not code:
        raise ValidationError("Currency code is required.")

    currency = resolve_fx_currency(code)

    if not currency:
        raise ValidationError(f"Invalid or unsupported currency code: '{code}'")

    return currency

def resolve_country(code: str | None) -> Country | None:
    """
    Universal resolver for ISO-3166 alpha-2 country codes.
    Normalizes casing and returns a Country instance or None.
    """
    if not code:
        return None
    
    code = code.upper().strip()
    return Country.objects.filter(code=code).first()

def validate_country_code(code: str):
    """
    Strict validator for ISO-3166 country codes.
    Uses resolve_country() but raises ValidationError if not found.
    """
    if not code:
        raise ValidationError(f"Country Code is required.")
    
    country = resolve_country(code)
    if not country:
        raise ValidationError(f"Invalid or unsupported country code: '{code}'")
    
    return country