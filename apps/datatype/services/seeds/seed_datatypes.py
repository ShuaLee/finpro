from datatype.models import DataType
from datatype.config.system_datatypes import SYSTEM_DATATYPES


def seed_datatypes():
    """
    Create or update system DataTypes.
    Returns the number of items created.
    """
    created_count = 0

    for dt in SYSTEM_DATATYPES:
        obj, created = DataType.objects.update_or_create(
            slug=dt["slug"],
            defaults={
                "name": dt["name"],
                "description": dt.get("description", ""),
                "supports_length": dt["supports_length"],
                "supports_decimals": dt["supports_decimals"],
                "supports_numeric_limits": dt["supports_numeric_limits"],
                "supports_regex": dt["supports_regex"],
                "is_system": True,
            },
        )

        if created:
            created_count += 1

    return created_count
