from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.apps import apps
from django.core.exceptions import ValidationError


IMPLICIT_IDENTIFIERS = {"fx_rate"}


def is_implicit_identifier(identifier: str) -> bool:
    return identifier in IMPLICIT_IDENTIFIERS


def _formula_definition_model():
    try:
        return apps.get_model("formulas", "FormulaDefinition")
    except (LookupError, ValueError):
        return None


def is_formulas_available() -> bool:
    return _formula_definition_model() is not None


def resolve_formula_definition(*, identifier: str, asset_type, owner=None):
    """
    Resolve a FormulaDefinition for an asset type.

    Resolution order:
    1. owner-specific definition (if owner provided)
    2. system definition (owner is null)
    """
    FormulaDefinition = _formula_definition_model()
    if FormulaDefinition is None:
        return None

    qs = FormulaDefinition.objects.filter(
        identifier=identifier,
        asset_type=asset_type,
    )

    if owner is not None and "owner" in {f.name for f in FormulaDefinition._meta.fields}:
        owned = qs.filter(owner=owner).first()
        if owned:
            return owned

    return qs.filter(owner__isnull=True).first()


def formula_dependencies(*, identifier: str, asset_type, owner=None) -> list[str]:
    definition = resolve_formula_definition(
        identifier=identifier,
        asset_type=asset_type,
        owner=owner,
    )
    if not definition:
        return []
    return list(getattr(definition.formula, "dependencies", []))


def resolve_inputs(
    *,
    formula,
    context: dict[str, Any],
    allow_missing: bool = False,
    default_missing: Decimal | int | float | None = None,
) -> dict[str, Decimal]:
    try:
        from formulas.services.formula_resolver import FormulaResolver
    except Exception:
        resolved: dict[str, Decimal] = {}
        for identifier in getattr(formula, "dependencies", []):
            if identifier not in context or context[identifier] is None:
                if not allow_missing:
                    raise ValidationError(
                        f"Missing required dependency '{identifier}' for formula '{formula.identifier}'."
                    )
                resolved[identifier] = Decimal(default_missing or 0)
                continue
            try:
                resolved[identifier] = Decimal(context[identifier])
            except Exception as exc:
                raise ValidationError(
                    f"Invalid value for dependency '{identifier}'."
                ) from exc
        return resolved

    return FormulaResolver.resolve_inputs(
        formula=formula,
        context=context,
        allow_missing=allow_missing,
        default_missing=default_missing,
    )


def evaluate_formula(*, formula, context: dict[str, Decimal]) -> Decimal:
    try:
        from formulas.services.formula_evaluator import FormulaEvaluator
    except Exception as exc:
        raise ValidationError("Formula evaluator is unavailable.") from exc
    return FormulaEvaluator.evaluate(formula=formula, context=context)
