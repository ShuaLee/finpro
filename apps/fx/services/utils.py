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

def resolve_country(code: str | None) -> Country | None:
    """
    Universal resolver for ISO-3166 alpha-2 country codes.
    Normalizes casing and returns a Country instance or None.
    """
    if not code:
        return None
    
    code = code.upper().strip()
    return Country.objects.filter(code=code).first()