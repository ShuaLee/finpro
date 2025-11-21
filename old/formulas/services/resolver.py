from django.contrib.contenttypes.models import ContentType
from formulas.services.evaluator import FormulaEvaluator

class FormulaResolver:
    def __init__(self, holding, schema):
        self.holding = holding
        self.schema = schema

    def build_context(self, formula):
        """
        Build the identifier -> value context for evaluating a formula.
        Pulls from SCVs first, then falls back to holding logic.
        """
        context = {}

        for dep in (formula.dependencies or []):
            # Find the matching column in this schema
            column = self.schema.columns.filter(identifier=dep).first()
            if not column:
                context[dep] = None
                continue

            # Find SCV for this holding + column
            scv = column.values.filter(
                account_ct=ContentType.objects.get_for_model(self.holding),
                account_id=self.holding.id,
            ).first()

            if scv and scv.is_edited:
                context[dep] = scv.get_value()
            else:
                # ⚡ recursive: resolve using column’s normal rules
                from schemas.services.schema_engine import HoldingSchemaEngine
                engine = HoldingSchemaEngine(self.holding, self.schema.schema_type)
                context[dep] = engine.get_configured_value(column)

        return context

    def evaluate(self, formula, constraints=None):
        """
        Evaluate a formula for this holding + schema.
        """
        values = self.build_context(formula)
        evaluator = FormulaEvaluator(formula, values, constraints=constraints)
        return evaluator.eval()