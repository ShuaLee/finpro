from django.db import transaction
from schemas.constants import STOCK_SCHEMA_COLUMNS_CATALOG
from schemas.models import StockPortfolioSC
import re


def extract_variables_from_formula(formula):
    """
    Extract variable names from a formula string.
    Supports alphanumeric and underscores.
    Example: "quantity * price + tax_rate" -> ['quantity', 'price', 'tax_rate']
    """
    return re.findall(r'[a-zA-Z_]\w*', formula)


def find_predefined_column_config(var_name):
    """
    Look up a predefined column config form STOCK_SCHEMA_COLUMNS_CATALOG by variable name.
    Matching is case-insensitive and ignored spaces/underscores.
    """
    normalized_var = var_name.lower().replace('_', '').strip()
    for col in STOCK_SCHEMA_COLUMNS_CATALOG:
        normalized_title = col['title'].lower().replace(' ', '')
        if normalized_var == normalized_title:
            return col
    return None


@transaction.atomic
def ensure_columns_for_formula(schema, formula):
    """
    Ensure all variables in formula exist as columns in the schema.
    If missing:
        - Check STOCK_SCHEMA_COLUMNS_CATALOG
        - Else create as custom column
    Returns a list of created columns.
    """
    variables = extract_variables_from_formula(formula)

    # Collect normalized existing titles
    existing_titles = [c.title.lower().replace(' ', '_')
                       for c in schema.columns.all()]

    created_columns = []

    for var in variables:
        if var.lower() not in existing_titles:
            # Try predefined column config
            predefined = find_predefined_column_config(var)
            if predefined:
                col = StockPortfolioSC.objects.create(
                    schema=schema,
                    # remove is_default
                    **{k: v for k, v in predefined.items() if k != 'is_default'}
                )
            else:
                # Create as custom column
                normalized_title = var.replace('_', ' ').title()
                col = StockPortfolioSC.objects.create(
                    schema=schema,
                    title=normalized_title,
                    data_type='decimal',
                    source='custom',
                    editable=True,
                    is_deletable=True,
                )

            created_columns.append(col)

    return created_columns
