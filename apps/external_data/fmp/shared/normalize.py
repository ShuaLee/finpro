from decimal import Decimal, InvalidOperation


def normalize_fmp_data(raw: dict, field_map: dict) -> dict:
    """
    Normalize raw FMP JSON to match our model fields using a field map.
    Handles decimals, booleans, and null safety.
    """
    result = {}
    for fmp_key, model_field in field_map.items():
        value = raw.get(fmp_key)

        # Skip empty/null
        if value in ("", None):
            continue

        # ✅ Handle booleans explicitly
        if isinstance(value, bool):
            result[model_field] = value
            continue

        # ✅ Handle numbers as Decimals
        if isinstance(value, (float, int)):
            try:
                value = Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError):
                pass

        result[model_field] = value

    return result
