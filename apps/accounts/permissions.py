# accounts/permissions.py
from rest_framework.permissions import BasePermission

class IsAccountOwner(BasePermission):
    """
    Custom permission: only the owner of the account can modify/view it.
    Works for:
    - SelfManagedAccount
    - ManagedAccount
    - StorageFacility
    """

    def has_object_permission(self, request, view, obj):
        # For SelfManagedAccount or ManagedAccount
        if hasattr(obj, 'stock_portfolio'):
            return obj.stock_portfolio.portfolio.profile.user == request.user

        # For StorageFacility (metal account)
        if hasattr(obj, 'metals_portfolio'):
            return obj.metals_portfolio.portfolio.profile.user == request.user

        return False
