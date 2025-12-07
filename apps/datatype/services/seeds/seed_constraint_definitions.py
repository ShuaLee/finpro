from datatype.models import DataType, ConstraintType, ConstraintDefinition
from datatype.config.system_constraint_definitions import SYSTEM_CONSTRAINT_DEFINITIONS


def seed_constraint_definitions():
    created_count = 0

    for cfg in SYSTEM_CONSTRAINT_DEFINITIONS:

        dt = DataType.objects.get(slug=cfg["data_type"])
        ct = ConstraintType.objects.get(slug=cfg["constraint_type"])

        obj, created = ConstraintDefinition.objects.update_or_create(
            data_type=dt,
            constraint_type=ct,
            defaults={
                "default_value": cfg["default"],
                "is_system": True,
            }
        )

        if created:
            created_count += 1

    return created_count
