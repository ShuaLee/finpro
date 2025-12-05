from assets.models.types.real_estate import RealEstateType
from assets.config.real_estate_types import SYSTEM_REAL_ESTATE_TYPES


def seed_real_estate_types():
    """
    Seeds the system real estate types from config.
    """
    count = 0

    for name, description in SYSTEM_REAL_ESTATE_TYPES:
        _, created = RealEstateType.objects.update_or_create(
            name=name,
            is_system=True,
            defaults={
                "description": description,
                "created_by": None
            }
        )
        if created:
            count += 1

    return count
