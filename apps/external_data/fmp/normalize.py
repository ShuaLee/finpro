from decimal import Decimal, InvalidOperation
import datetime


def _to_decimal(value, default=None):
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _to_int(value, default=None):
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _to_str(value, default=None):
    return str(value) if value is not None else default


def _to_date(value, default=None):
    try:
        return datetime.date.fromisoformat(value) if value else default
    except (ValueError, TypeError):
        return default


# Generic normalizer
def normalize_fmp_data(data: dict, field_map: dict) -> dict:
    """
    Normalize FMP API data into model-ready fields.

    Args:
        data: raw dict from FMP
        field_map: mapping of model_field -> (fmp_key, transformer_fn)

    Returns:
        dict of normalized {model_field: value}
    """
    normalized = {}
    for model_field, (fmp_key, transformer) in field_map.items():
        raw_value = data.get(fmp_key)
        try:
            normalized[model_field] = transformer(
                raw_value) if raw_value is not None else None
        except Exception:
            normalized[model_field] = None
    return normalized
