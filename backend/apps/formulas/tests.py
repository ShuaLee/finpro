from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from formulas.services.formula_evaluator import FormulaEvaluator
from formulas.services.formula_resolver import FormulaResolver
from formulas.services.system_registry import SystemFormulaRegistry


@dataclass
class DummyFormula:
    identifier: str
    expression: str
    dependencies: list[str]
    decimal_places: int | None = None


class FormulaEvaluatorTests(SimpleTestCase):
    def test_evaluate_basic_expression(self):
        formula = DummyFormula(
            identifier="current_value",
            expression="quantity * price",
            dependencies=["quantity", "price"],
            decimal_places=2,
        )
        result = FormulaEvaluator.evaluate(
            formula=formula,
            context={"quantity": Decimal("2"), "price": Decimal("10.125")},
        )
        self.assertEqual(result, Decimal("20.25"))

    def test_evaluate_rejects_divide_by_zero(self):
        formula = DummyFormula(
            identifier="bad_division",
            expression="quantity / price",
            dependencies=["quantity", "price"],
        )
        with self.assertRaises(ValidationError):
            FormulaEvaluator.evaluate(
                formula=formula,
                context={"quantity": Decimal("2"), "price": Decimal("0")},
            )

    def test_evaluate_rejects_unsupported_nodes(self):
        formula = DummyFormula(
            identifier="unsafe",
            expression="__import__('os').system('echo hi')",
            dependencies=[],
        )
        with self.assertRaises(ValidationError):
            FormulaEvaluator.evaluate(formula=formula, context={})


class FormulaResolverTests(SimpleTestCase):
    def test_resolve_inputs_missing_dependency_strict(self):
        formula = DummyFormula(
            identifier="market_value",
            expression="quantity * price",
            dependencies=["quantity", "price"],
        )
        with self.assertRaises(ValidationError):
            FormulaResolver.resolve_inputs(
                formula=formula,
                context={"quantity": Decimal("1")},
                allow_missing=False,
            )

    def test_resolve_inputs_missing_dependency_auto_expand(self):
        formula = DummyFormula(
            identifier="market_value",
            expression="quantity * price",
            dependencies=["quantity", "price"],
        )
        resolved = FormulaResolver.resolve_inputs(
            formula=formula,
            context={"quantity": Decimal("1")},
            allow_missing=True,
            default_missing=Decimal("0"),
        )
        self.assertEqual(resolved["price"], Decimal("0"))


class SystemRegistryTests(SimpleTestCase):
    def test_registry_consistency(self):
        all_identifiers = SystemFormulaRegistry.all()
        self.assertIn("current_value", all_identifiers)
        self.assertTrue(SystemFormulaRegistry.is_reserved("market_value"))
        self.assertFalse(SystemFormulaRegistry.is_reserved("user_custom_metric"))
