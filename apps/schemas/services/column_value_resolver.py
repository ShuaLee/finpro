from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from schemas.models import SchemaColumnValue
from decimal import Decimal


def resolve_column_value(holding, column, fallback_to_default):
    """
    Resolves the current value for a schema column for a given holding.

    Resolution order:
    1. SchemaColumnValue (if edited)
    2. Holding.<source_field>
    3. Holding.asset.<source_field>
    4. holding.<formula_method>() if present
    5. Evaluate formula_expression (future)
    """

    # 1. Check for SCV override
    content_type = ContentType.objects.get_for_model(holding)
    scv = SchemaColumnValue.objects.filter(
        column=column,
        account_ct=content_type,
        account_id=holding.id,
    ).first()

    if scv and scv.is_edited:
        return cast_value(scv.value, column)

    # 2. Get value from holding or asset
    field = column.source_field
    if column.source == "holding":
        return getattr(holding, field, None)
    elif column.source == "asset":
        return getattr(getattr(holding, holding.asset_field_name), field, None)

    # 3. Use backend formula method
    if column.source == "calculated" and column.formula_method:
        method = getattr(holding, column.formula_method, None)
        if method and callable(method):
            return method()

    # 4. (Optional future) Evaluate formula_expression

    if fallback_to_default:
        return None  # Fallback value if nothing found

    raise ValueError(f"Could not resolve value for column {column.title}")


def cast_value(value, column):
    """
    Casts the value from string/JSON into the correct data type.
    """
    try:
        if value is None:
            return None
        if column.data_type == "decimal":
            return Decimal(value)
        elif column.data_type == "integer":
            return int(value)
        elif column.data_type == "date":
            return parse_date(value)
        elif column.data_type == "datetime":
            return parse_datetime(value)
        elif column.data_type == "time":
            return parse_time(value)
        return value
    except Exception as e:
        # Log, raise, or return raw value
        return value
