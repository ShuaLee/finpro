from accounts.models import StorageFacility
from django.core.exceptions import ValidationError

def create_storage_facility(user, data):
    """
    Creates a StorageFacility account for the user's MetalPortfolio.
    """
    if not hasattr(user.profile.portfolio, 'metalportfolio'):
        raise ValidationError("Metal portfolio does not exist for this user.")

    metal_portfolio = user.profile.portfolio.metalportfolio
    return StorageFacility.objects.create(metals_portfolio=metal_portfolio, **data)

def get_storage_facilities(user):
    """
    Returns all StorageFacility accounts for the user's MetalPortfolio.
    """
    if not hasattr(user.profile.portfolio, 'metalportfolio'):
        return StorageFacility.objects.none()
    return StorageFacility.objects.filter(metals_portfolio=user.profile.portfolio.metalportfolio)
