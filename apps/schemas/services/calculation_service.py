import re
from django.db import transaction
from simpleeval import simple_eval
from schemas.models import StockPortfolioSC, StockPortfolioSCV
from schemas.constants import STOCK_SCHEMA_COLUMNS_CATALOG


def extract_variables_from_formula(formula):
    return re.findall(r'[a-zA-Z_]\w*', formula)


def find_predefined_column_config(var_name):
    normalized_var = var_name.lower().replace('_', '').strip()
    for col in STOCK_SCHEMA_COLUMNS_CATALOG:
        normalized_title = col['title'].lower().replace(' ', '')
        if normalized_var == normalized_title:
            return col
    return None


@transaction.atomic
def ensure_columns_for_formula(schema, formula):
    variables = extract_variables_from_formula(formula)
    existing_titles = [c.title.lower().replace(' ', '_')
                       for c in schema.columns.all()]
    created_columns = []

    for var in variables:
        if var.lower() not in existing_titles:
            predefined = find_predefined_column_config(var)
            if predefined:
                col = StockPortfolioSC.objects.create(
                    schema=schema,
                    **{k: v for k, v in predefined.items() if k != 'is_default'}
                )
            else:
                col = StockPortfolioSC.objects.create(
                    schema=schema,
                    title=var.replace('_', ' ').title(),
                    data_type='decimal',
                    source='custom',
                    editable=True,
                    is_deletable=True
                )
            created_columns.append(col)
    return created_columns


@transaction.atomic
def add_calculated_column(schema, title, formula):
    if not title or not formula:
        raise ValueError("Title and formula are required.")
    ensure_columns_for_formula(schema, formula)
    return StockPortfolioSC.objects.create(
        schema=schema,
        title=title,
        data_type='decimal',
        source='calculated',
        formula=formula,
        editable=False,
        is_deletable=True
    )


def build_context(schema, holding):
    """
    Efficiently build variable context for a holding.
    """
    values = StockPortfolioSCV.objects.filter(
        holding=holding).select_related('column')
    context = {}
    for v in values:
        key = v.column.title.lower().replace(' ', '_')
        try:
            context[key] = float(v.get_value() or 0)
        except (ValueError, TypeError):
            context[key] = 0
    return context


def recalculate_calculated_columns(schema, holding):
    context = build_context(schema, holding)
    for col in schema.columns.filter(source='calculated'):
        if col.formula:
            try:
                result = simple_eval(col.formula, names=context, functions={})
            except Exception:
                result = None
            col.values.update_or_create(
                holding=holding,
                defaults={'value': str(
                    result) if result is not None else None, 'is_edited': False}
            )
