from decimal import Decimal, ROUND_HALF_UP


def apply_precision(value: Decimal, operands: list[Decimal], constraints: dict) -> Decimal:
    # Rule 1: get max decimal places from input
    max_places = max((abs(val.as_tuple().exponent)
                     for val in operands if val is not None), default=2)

    # Rule 2: constraints override
    places = constraints.get("decimal_places", max_places)

    quantizer = Decimal("1." + ("0" * places)) if places > 0 else Decimal("1")
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)
