from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from assets.models.base import HoldingThemeValue
from schemas.models import SchemaColumnValue
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from simpleeval import simple_eval
import re


def resolve_column_value(holding, column, fallback_to_default):
    content_type = ContentType.objects.get_for_model(holding)

    # 1️⃣ Edited SchemaColumnValue
    scv = SchemaColumnValue.objects.filter(
        column=column,
        account_ct=content_type,
        account_id=holding.id,
    ).first()
    if scv and scv.is_edited:
        return format_value(cast_value(scv.value, column), column)

    # 2️⃣ InvestmentTheme-based resolution
    if column.investment_theme:
        htv = HoldingThemeValue.objects.filter(
            holding_ct=content_type,
            holding_id=holding.id,
            theme=column.investment_theme
        ).first()
        if htv:
            raw = htv.get_value()
            return format_value(cast_value(raw, column), column)

    # 3️⃣ Holding source
    if column.source == "holding":
        raw = getattr(holding, column.source_field, None)
        return format_value(_default_if_none(raw, column), column)

    # 4️⃣ Asset source
    elif column.source == "asset":
        asset = getattr(holding, holding.asset_field_name, None)
        if asset:
            raw = getattr(asset, column.source_field, None)
            return format_value(_default_if_none(raw, column), column)

    # 5️⃣ Formula method
    if column.source == "calculated":
        if column.formula_method:
            method = getattr(holding, column.formula_method, None)
            if method and callable(method):
                try:
                    return format_value(method(), column)
                except Exception as e:
                    return _fallback_default(column)

        # 6️⃣ Formula expression
        elif column.formula_expression:
            val = evaluate_symbolic_formula(holding, column.formula_expression)
            return format_value(_default_if_none(val, column), column)

    if fallback_to_default:
        return _fallback_default(column)

    raise ValueError(f"Could not resolve value for column {column.title}")


def _default_if_none(val, column):
    if val is not None:
        return val
    return _fallback_default(column)


def _fallback_default(column):
    if column.data_type == "decimal":
        dp = int(column.constraints.get("decimal_places", 2))
        return Decimal("0").quantize(Decimal(f"1.{'0'*dp}"))
    elif column.data_type == "string":
        return "-"
    return None

def cast_value(value, column):
    """
    Converts a raw value into the expected Python type based on the column's data_type.
    """
    if value is None:
        return None

    try:
        dt = column.data_type

        if dt == "decimal":
            return Decimal(value)

        elif dt == "integer":
            return int(value)

        elif dt == "date":
            return parse_date(value)

        elif dt == "datetime":
            return parse_datetime(value)

        elif dt == "time":
            return parse_time(value)

        elif dt in ["string", "url"]:
            return str(value)

        else:
            # Unknown type — fallback to raw
            return value

    except (ValueError, TypeError, InvalidOperation):
        return value


def format_value(value, column):
    if value is None:
        return None

    dt = column.data_type

    if dt == "decimal" and isinstance(value, Decimal):
        places = column.decimal_places or 2
        quant = Decimal(f"1.{'0'*places}")
        return value.quantize(quant, rounding=ROUND_HALF_UP)

    elif dt == "date" and isinstance(value, date):
        return value.isoformat()

    elif dt == "datetime" and isinstance(value, datetime):
        return value.isoformat()

    elif dt == "time" and isinstance(value, time):
        return value.strftime("%H:%M:%S")

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
