from fx.models import FXCurrency


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
