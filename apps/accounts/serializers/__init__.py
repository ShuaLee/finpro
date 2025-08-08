# apps/accounts/serializers/__init__.py

# New unified stock account serializers
from .stocks import (
    StockAccountBaseSerializer,
    StockAccountCreateSerializer,
)

# Metals serializers (unchanged)
from .metals import (
    StorageFacilitySerializer,
    StorageFacilityCreateSerializer,
)

# ---- Backward-compat aliases (remove after refactor) ----
# If any old code imports the legacy names, keep them working for now.
SelfManagedAccountSerializer = StockAccountBaseSerializer
SelfManagedAccountCreateSerializer = StockAccountCreateSerializer
ManagedAccountSerializer = StockAccountBaseSerializer
ManagedAccountCreateSerializer = StockAccountCreateSerializer
# ---------------------------------------------------------

__all__ = [
    # New canonical names
    "StockAccountBaseSerializer",
    "StockAccountCreateSerializer",

    # Metals
    "StorageFacilitySerializer",
    "StorageFacilityCreateSerializer",
]
