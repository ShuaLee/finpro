from decimal import Decimal
from .constants import PREDEFINED_COLUMNS
from .models import SchemaColumn
import math
import re

def set_nested_attr(obj, attr_path, value):
    """Sets a value on a nested attribute path like 'holding.stock.price'."""
    attrs = attr_path.split('.')
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)


def get_predefined_column_metadata(source, field):
    for col in PREDEFINED_COLUMNS.get(source, []):
        if col['field'] == field:
            return {
                'label': col['label'],
                'data_type': col['type']
            }
    return None


def ensure_required_columns(schema, formula):
    """
    For a given formula, ensure all required source columns exist in the schema.
    """
    referenced_fields = set(re.findall(r'\b\w+\b', formula))

    for source_type, fields in PREDEFINED_COLUMNS.items():
        for field in fields:
            if field['field'] in referenced_fields:
                exists = schema.columns.filter(
                    source=source_type,
                    source_field=field['field']
                ).exists()

                if not exists:
                    SchemaColumn.objects.create(
                        schema=schema,
                        name=field['label'],
                        data_type=field['type'],
                        source_field=field['field'],
                        editable=field.get('editable', True)
                    )


def evaluate_formula(formula, instance):
    """
    Evaluates a formula like 'shares * last_price' using values
    from a StockHolding instance and its related stock.
    """
    context = {}

    # Build context from holding
    for item in PREDEFINED_COLUMNS['holding']:
        context[item['field']] = getattr(instance, item['field'], None)

    # Build context from stock
    stock = getattr(instance, 'stock', None)
    if stock:
        for item in PREDEFINED_COLUMNS['stock']:
            context[item['field']] = getattr(stock, item['field'], None)

    # Clean None values
    safe_context = {k: v for k, v in context.items() if v is not None}

    try:
        return eval(formula, {"__builtins__": {}, "math": math, "Decimal": Decimal}, safe_context)
    except Exception:
        return None
