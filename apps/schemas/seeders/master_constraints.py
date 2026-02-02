from decimal import Decimal

from schemas.models import MasterConstraint


def seed_master_constraints():
    """
    Seed system-level MasterConstraints.

    These define how SchemaColumnValues are:
    - formatted
    - validated on user input
    - displayed

    Safe to re-run.
    """

    constraints = [
        # ==================================================
        # DECIMAL (Number)
        # ==================================================
        {
            "name": "decimal_places",
            "label": "Decimal Places",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "default_decimal": Decimal("2"),
            "min_decimal": Decimal("0"),
            "max_decimal": Decimal("30"),
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "default_decimal": None,
            "min_decimal": Decimal("-1e18"),
            "max_decimal": Decimal("1e18"),
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "default_decimal": None,
            "min_decimal": Decimal("-1e18"),
            "max_decimal": Decimal("1e18"),
        },

        # ==================================================
        # PERCENT (stored as decimal, displayed as %)
        # ==================================================
        {
            "name": "decimal_places",
            "label": "Decimal Places",
            "applies_to": MasterConstraint.AppliesTo.PERCENT,
            "default_decimal": Decimal("2"),
            "min_decimal": Decimal("0"),
            "max_decimal": Decimal("6"),
        },

        # ==================================================
        # STRING
        # ==================================================
        {
            "name": "max_length",
            "label": "Maximum Length",
            "applies_to": MasterConstraint.AppliesTo.STRING,
            "default_string": "255",
        },
        {
            "name": "enum",
            "label": "Allowed Values",
            "applies_to": MasterConstraint.AppliesTo.STRING,
            "default_string": None,
        },

        # ==================================================
        # BOOLEAN
        # ==================================================
        {
            "name": "boolean",
            "label": "Boolean",
            "applies_to": MasterConstraint.AppliesTo.BOOLEAN,
            "default_string": None,
        },

        # ==================================================
        # DATE
        # ==================================================
        {
            "name": "min_date",
            "label": "Minimum Date",
            "applies_to": MasterConstraint.AppliesTo.DATE,
            "default_date": None,
        },
        {
            "name": "max_date",
            "label": "Maximum Date",
            "applies_to": MasterConstraint.AppliesTo.DATE,
            "default_date": None,
        },
    ]

    for data in constraints:
        MasterConstraint.objects.update_or_create(
            name=data["name"],
            applies_to=data["applies_to"],
            defaults=data,
        )
