from decimal import Decimal, InvalidOperation


def normalize_fmp_data(raw: dict, field_map: dict) -> dict:
    """
    Normalize raw FMP keys into local model field names.
    """
    result: dict = {}
    for fmp_key, model_field in field_map.items():
        if fmp_key not in raw:
            continue

        value = raw.get(fmp_key)
        if value is None or value == "":
            continue

        if isinstance(value, bool):
            result[model_field] = value
            continue

        if isinstance(value, (float, int)):
            try:
                value = Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError):
                pass

        result[model_field] = value

    return result
