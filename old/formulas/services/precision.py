from formulas.models import Formula
from decimal import Decimal, ROUND_HALF_UP

def apply_precision(value: Decimal, formula: Formula, constraints: dict) -> Decimal:
    if formula.is_system:
        places = constraints.get("decimal_places", 2)  # system -> respect template
    else:
        places = 2  # custom -> always 2 by default
    
    quantizer = Decimal("1." + ("0" * places)) if places > 0 else Decimal("1")
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)
