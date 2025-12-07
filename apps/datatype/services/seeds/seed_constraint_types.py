from datatype.models import DataType, ConstraintType
from datatype.config.system_constraint_types import SYSTEM_CONSTRAINT_TYPES


def seed_constraint_types():
    created_count = 0

    for cfg in SYSTEM_CONSTRAINT_TYPES:

        # Look up the DataType used to validate the constraint's value
        value_dt = DataType.objects.get(slug=cfg["value_data_type"])

        ct, created = ConstraintType.objects.update_or_create(
            slug=cfg["slug"],
            defaults={
                "name": cfg["name"],
                "description": cfg.get("description", ""),
                "value_data_type": value_dt,
                "is_system": True,
            }
        )

        # Attach allowed DataTypes
        ct.applies_to.set(
            DataType.objects.filter(slug__in=cfg["applies_to"])
        )

        if created:
            created_count += 1

    return created_count
