from decimal import Decimal
from schemas.models.formula import Formula
from schemas.models.schema import SchemaColumn


class FormulaPrecisionResolver:
    """
    Determines the number of decimal places that a formula result
    should be rounded/formatted to.
    """

    @staticmethod
    def get_precision(formula: Formula, target_column: SchemaColumn = None) -> int:
        """
        Determine precision rules:

            SYSTEM FORMULA:
                - If attached to a column with a decimal_places constraint → use it
                - Else defaults to 2

            USER FORMULA:
                - Must obey formula.decimal_places if set
                - Else defaults to 2
        """

        # ---------------------------------------------
        # 1. USER FORMULA → explicit override
        # ---------------------------------------------
        if not formula.is_system:
            if formula.decimal_places is not None:
                return int(formula.decimal_places)
            return 2   # fallback

        # ---------------------------------------------
        # 2. SYSTEM FORMULA → check column constraints
        # ---------------------------------------------
        if target_column:
            dp_constraint = target_column.constraints_set.filter(
                name="decimal_places"
            ).first()

            if dp_constraint and dp_constraint.value:
                try:
                    return int(dp_constraint.value)
                except:
                    pass

        # fallback for system formulas
        return 2
