from schemas.models.formula import Formula


class FormulaPrecisionResolver:
    """
    Determines decimal precision for formula results.
    """

    @staticmethod
    def get_precision(formula: Formula, target_column=None) -> int:

        # ---------------- USER FORMULAS ----------------
        if not formula.is_system:
            return formula.decimal_places if formula.decimal_places is not None else 2

        # ---------------- SYSTEM FORMULAS ----------------
        if target_column is not None:
            constraint = target_column.constraints_set.filter(
                name="decimal_places"
            ).first()

            if constraint:
                value = constraint.get_typed_value()
                if value is not None:
                    return int(value)

        if formula.decimal_places is not None:
            return int(formula.decimal_places)

        return 2
