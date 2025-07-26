from django.db import transaction
from schemas.models import StockPortfolioSC
from schemas.services import ensure_columns_for_formula
from simpleeval import simple_eval


@transaction.atomic
def add_calculated_column(schema, title, formula):
    """
    Add a calculated column to the schema.
    Ensures all dependent columns exist first.
    """
    if not title or not formula:
        raise ValueError("Title and formula are required.")

    ensure_columns_for_formula(schema, formula)

    return StockPortfolioSC.objects.create(
        schema=schema,
        title=title,
        data_type='decimal',  # Always numeric for formulas
        source='calculated',
        formula=formula,
        editable=False,
        is_deletable=True
    )


def build_context(schema, holding):
    """
    Build a dictionary of normalized column names to their values for this holding.
    """
    context = {}
    for col in schema.columns.prefetch_related('values').all():
        scv = next((v for v in col.values.all()
                   if v.holding_id == holding.id), None)
        if scv:
            key = col.title.lower().replace(' ', '_')
            try:
                context[key] = float(scv.get_value() or 0)
            except (ValueError, TypeError):
                context[key] = 0
    return context


def recalculate_calculated_columns(schema, holding):
    """
    Recompute all calculated columns for a specific holding.
    """
    context = build_context(schema, holding)

    for col in schema.columns.filter(source='calculated'):
        if col.formula:
            try:
                result = simple_eval(col.formula, names=context, functions={})
            except Exception:
                result = None

            col.values.update_or_create(
                holding=holding,
                defaults={
                    'value': str(result) if result is not None else None,
                    'is_edited': False
                }
            )
