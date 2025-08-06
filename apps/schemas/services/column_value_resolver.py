from decimal import Decimal, ROUND_HALF_UP
from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from schemas.models import SchemaColumnValue
from simpleeval import simple_eval
import re


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
    content_type = ContentType.objects.get_for_model(holding)
    scv = SchemaColumnValue.objects.filter(
        column=column,
        account_ct=content_type,
        account_id=holding.id,
    ).first()

    if scv and scv.is_edited:
        return format_value(cast_value(scv.value, column), column)

    field = column.source_field
    if column.source == "holding":
        return format_value(getattr(holding, field, None), column)
    elif column.source == "asset":
        asset = getattr(holding, holding.asset_field_name, None)
        return format_value(getattr(asset, field, None), column) if asset else None

    if column.source == "calculated":
        if column.formula_method:
            method = getattr(holding, column.formula_method, None)
            if method and callable(method):
                return format_value(method(), column)
        elif column.formula_expression:
            return format_value(
                evaluate_symbolic_formula(holding, column.formula_expression),
                column
            )

    if fallback_to_default:
        return None

    raise ValueError(f"Could not resolve value for column {column.title}")


def cast_value(value, column):
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
    except Exception:
        return value


def format_value(value, column):
    if value is None:
        return None
    if column.data_type == "decimal" and isinstance(value, Decimal):
        places = column.decimal_places or 2
        quant = Decimal(f"1.{'0'*places}")
        return value.quantize(quant, rounding=ROUND_HALF_UP)
    return value


def evaluate_symbolic_formula(holding, formula: str):
    """
    Evaluate a user-defined symbolic formula like "quantity * price / 100".
    """
    # Extract variable names (e.g. quantity, price)
    variables = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", formula))
    values = {}

    from schemas.models import SchemaColumn

    # Look up columns that may match these variable names
    schema = holding.account.active_schema
    candidate_columns = schema.columns.filter(source_field__in=variables)

    for column in candidate_columns:
        val = resolve_column_value(holding, column, fallback_to_default=True)
        if val is None:
            val = 0
        values[column.source_field] = val

    try:
        result = simple_eval(formula, names=values)
        return Decimal(str(result))
    except Exception:
        return None
