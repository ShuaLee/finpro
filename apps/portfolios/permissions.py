from rest_framework.permissions import BasePermission

class IsPortfolioOwner(BasePermission):
    """
    Custom permission to allow only the portfolio's owner to view or edit.
    """

    def has_object_permission(self, request, view, obj):
        # obj can be Portfolio or StockPortfolio
        if hasattr(obj, "profile"): # Portfolio
            return obj.profile.user == request.user
        if hasattr(obj, "portfolio"): # BaseAssetPortfolios
            return obj.portfolio.profile.user == request.user
        return False
    