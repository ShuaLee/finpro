from schemas.models import Schema, SchemaColumnValue
from schemas.services.expression_evaluator import evaluate_expression
from asteval import Interpreter
from decimal import Decimal


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
    context = build_context(schema, account)

    for column in schema.columns.filter(source="calculated"):
        if column.formula:
            result = evaluate_expression(column.formula, context)

            SchemaColumnValue.objects.update_or_create(
                column=column,
                account_ct=account.__class__,
                account_id=account.id,
                defaults={
                    "value": str(result) if result is not None else None,
                    "is_edited": False,
                },
            )


def evaluate_expression(self, expression: str):
    """
    Evaluates a safe math expression using resolved variables.
    """
    variables = self.get_all_available_values()
    aeval = Interpreter()

    for key, val in variables.items():
        aeval.symtable[key] = val

    try:
        result = aeval(expression)
        print(f"🧮 Evaluated '{expression}' -> {result}")
        return result
    except Exception as e:
        print(f"❌ Formula eval failed: {expression} -> {e}")
        return None


def get_all_available_values(self):
    """
    Collect all values from known config sources.
    """
    values = {}

    for source in ["asset", "holding"]:
        config_group = self.config.get(source, {})
        for field, meta in config_group.items():
            val = self.resolve_value(meta.get("field_path"))
            try:
                values[field] = Decimal(str(val)) if val is not None else None
            except:
                values[field] = val

    return values
