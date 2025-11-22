from schemas.models.formula import Formula


def lookup_formula(identifier):
    try:
        return Formula.objects.get(identifier=identifier)
    except Formula.DoesNotExist:
        return None
