
class SystemFormulaRegistry:
    """
    Central registry for system-reserved formula identifiers.

    These identifiers:
    - are globally reserved
    - cannot be created by users
    - are relied upon by schemas and analytics
    """

    SYSTEM_IDENTIFIERS = {
        # Base computations used by schemas
        "quantity_times_price",
        "market_value_times_fx",
        "quantity_times_avg_price_times_fx",
        "current_value_minus_cost_basis",
        "unrealized_gain_over_cost_basis",
        "market_value",
        "current_value",
        "cost_basis",
        "unrealized_gain",
        "unrealized_gain_pct",

        # Core valuation
        "open_pnl",

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
        return identifier in cls.SYSTEM_IDENTIFIERS

    @classmethod
    def all(cls) -> set[str]:
        """
        Return all system-reserved identifiers.
        """
        return set(cls.SYSTEM_IDENTIFIERS)
