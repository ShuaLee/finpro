from decimal import Decimal

def normalize_constraints(value):
    """Recursively make constraints JSON-serializable."""
    if isinstance(value, Decimal):
        return float(value)  # or str(value) if you prefer exact
    if isinstance(value, dict):
        return {k: normalize_constraints(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_constraints(v) for v in value]
    return value
