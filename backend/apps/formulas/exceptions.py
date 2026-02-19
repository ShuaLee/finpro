class FormulaError(Exception):
    """
    Base exception for all formula-related errors.
    """
    pass


# ---------------------------------------------------------------------
# Formula lifecycle errors
# ---------------------------------------------------------------------

class FormulaCreationError(FormulaError):
    """
    Raised when a formula cannot be created.
    """
    pass


class FormulaUpdateError(FormulaError):
    """
    Raised when a formula cannot be updated.
    """
    pass


class FormulaDeletionError(FormulaError):
    """
    Raised when a formula cannot be deleted.
    """
    pass


# ---------------------------------------------------------------------
# Permission / ownership errors
# ---------------------------------------------------------------------

class FormulaPermissionError(FormulaError):
    """
    Raised when a user attempts an unauthorized action.
    """
    pass


# ---------------------------------------------------------------------
# Definition errors
# ---------------------------------------------------------------------

class FormulaDefinitionError(FormulaError):
    """
    Base error for formula definition issues.
    """
    pass


class FormulaDefinitionNotFound(FormulaDefinitionError):
    """
    Raised when a definition cannot be resolved.
    """
    pass


# ---------------------------------------------------------------------
# Dependency errors
# ---------------------------------------------------------------------

class FormulaDependencyError(FormulaError):
    """
    Raised when formula dependencies cannot be satisfied.
    """
    pass


class MissingFormulaDependency(FormulaDependencyError):
    """
    Raised when required dependencies are missing.
    """

    def __init__(self, *, formula_identifier, missing_identifiers):
        self.formula_identifier = formula_identifier
        self.missing_identifiers = set(missing_identifiers)

        super().__init__(
            f"Formula '{formula_identifier}' is missing dependencies: "
            f"{', '.join(sorted(self.missing_identifiers))}"
        )


# ---------------------------------------------------------------------
# Evaluation errors
# ---------------------------------------------------------------------

class FormulaEvaluationError(FormulaError):
    """
    Raised when a formula fails during evaluation.
    """
    pass
