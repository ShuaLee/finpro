from schemas.models import MasterConstraint


def seed_master_constraints():
    """
    Seed system-level MasterConstraints.

    Safe to re-run.
    """

    constraints = [
        {
            "name": "decimal_places",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "label": "Decimal Places",
            "default_decimal": 2,
            "min_decimal": 0,
            "max_decimal": 10,
        },
        {
            "name": "min_value",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "label": "Minimum Value",
            "default_decimal": 0,
            "min_decimal": -10_000_000,
            "max_decimal": 10_000_000,
        },
        {
            "name": "max_value",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "label": "Maximum Value",
            "default_decimal": 10_000_000,
            "min_decimal": 0,
            "max_decimal": 1_000_000_000,
        },
        {
            "name": "max_length",
            "applies_to": MasterConstraint.AppliesTo.STRING,
            "label": "Maximum Length",
            "default_string": "255",
        },
    ]

    for data in constraints:
        MasterConstraint.objects.update_or_create(
            name=data["name"],
            defaults=data,
        )
