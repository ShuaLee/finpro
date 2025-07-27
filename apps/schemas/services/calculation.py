from simpleeval import simple_eval
from schemas.models.core import Schema, SchemaColumnValue


def build_context(schema: Schema, account):
    """
    Builds a context dictionary for formula evaluation based on column values for a given account.
    """
    context = {}
    values = SchemaColumnValue.objects.filter(
        account_ct__model=account.__class__.__name__.lower(), account_id=account.id)

    for value in values.select_related('column'):
        key = value.column.title.lower().replace(" ", "_")
        try:
            context[key] = float(value.value) if value.value is not None else 0
        except ValueError:
            context[key] = 0
    return context


def recalculate_calculated_columns(schema: Schema, account):
    """
    Recalculates all calculated columns for a given account.
    """
    context = build_context(schema, account)
    for column in schema.columns.filter(source="calculated"):
        if column.formula:
            try:
                result = simple_eval(column.formula, names=context)
            except Exception:
                result = None

            SchemaColumnValue.objects.update_or_create(
                column=column,
                account_ct=account.__class__,
                account_id=account.id,
                defaults={"value": str(
                    result) if result is not None else None, "is_edited": False},
            )
