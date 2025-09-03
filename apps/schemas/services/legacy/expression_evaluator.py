from asteval import Interpreter


def evaluate_expression(expression: str, variables: dict):
    """
    Safely evaluates a math expression using asteval and the given variable context.
    """
    aeval = Interpreter()

    for key, val in variables.items():
        aeval.symtable[key] = val

    try:
        return aeval(expression)
    except Exception as e:
        print(f"Formula eval failed: {expression} -> {e}")
        return None
