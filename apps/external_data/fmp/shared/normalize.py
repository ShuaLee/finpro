from decimal import Decimal, InvalidOperation


def normalize_fmp_data(raw: dict, field_map: dict) -> dict:
    """
    Normalize raw FMP JSON to match our model fields using a field map.
    Handles decimals, booleans, and null safety.
    """
    result = {}
    for fmp_key, model_field in field_map.items():
        # Skip missing keys
        if fmp_key not in raw:
            continue

        value = raw.get(fmp_key)

        # ✅ Explicitly handle None and empty strings
        if value is None or value == "":
            continue

        # ✅ Keep booleans intact (don’t drop False)
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
