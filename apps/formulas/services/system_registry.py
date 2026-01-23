

class SystemFormulaRegistry:
    """
    Central registry for system-reserved formula identifiers.

    These identifiers:
    - are globally reserved
    - cannot be created by users
    - are relied upon by schemas and analytics
    """

    SYSTEM_IDENTIFERS = {
        # Core valuation
        "current_value",
        "cost_basis",
        "open_pnl",
        "unrealized_gain",

        # Allocation / weighting
        "portfolio_weight",

        # You can add more over time, but NEVER remove or rename
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def is_reserved(cls, identifier: str) -> bool:
        """
        Return True if the identifier is reserved by the system.
        """
        if not identifier:
            return False
        return identifier in cls.SYSTEM_IDENTIFERS

    @classmethod
    def all(cls) -> set[str]:
        """
        Return all system-reserved identifiers.
        """
        return set(cls.SYSTEM_IDENTIFIERS)
