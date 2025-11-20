from schemas.models.formula import Formula
from schemas.models.schema import SchemaColumn


class FormulaPrecisionResolver:
    """
    Determines how many decimal places a formula result should be rounded to.

    Priority rules:

        USER FORMULAS:
            1. formula.decimal_places (if set)
            2. fallback: 2

        SYSTEM FORMULAS:
            1. target column’s decimal_places constraint (if exists)
            2. formula.decimal_places (optional system override)
            3. fallback: 2
    """

    @staticmethod
    def get_precision(formula: Formula, target_column: SchemaColumn = None) -> int:
        # -----------------------------------------------------
        # USER FORMULAS → user explicitly decides precision
        # -----------------------------------------------------
        if not formula.is_system:
            if formula.decimal_places is not None:
                try:
                    return int(formula.decimal_places)
                except Exception:
                    pass
            return 2

        # -----------------------------------------------------
        # SYSTEM FORMULAS → check column constraint first
        # (This matches how SCV display works)
        # -----------------------------------------------------
        if target_column is not None:
            constraint = target_column.constraints_set.filter(
                name="decimal_places"
            ).first()

            if constraint:
                # Prefer overridden value (user-modifiable)
                if constraint.value not in (None, ""):
                    try:
                        return int(constraint.value)
                    except Exception:
                        pass

                # Otherwise fall back to template default_value
                if constraint.default_value not in (None, ""):
                    try:
                        return int(constraint.default_value)
                    except Exception:
                        pass

        # -----------------------------------------------------
        # SYSTEM formula fallback to formula.decimal_places
        # -----------------------------------------------------
        if formula.decimal_places is not None:
            try:
                return int(formula.decimal_places)
            except Exception:
                pass

        # -----------------------------------------------------
        # Universal safe fallback
        # -----------------------------------------------------
        return 2
