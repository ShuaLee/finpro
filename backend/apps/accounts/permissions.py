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
        # If obj is Account
        if hasattr(obj, 'portfolio'):
            return obj.portfolio.profile.user == request.user

        # If obj is Holding
        if hasattr(obj, 'account'):
            return obj.account.portfolio.profile.user == request.user

        return False
