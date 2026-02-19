"""
Legacy module kept to avoid import breakage.

The previous metals-specific account models were removed in favor of the
generic Account/Holding model set.
"""

from accounts.serializers.stocks import AccountSerializer, HoldingSerializer

__all__ = ["AccountSerializer", "HoldingSerializer"]
