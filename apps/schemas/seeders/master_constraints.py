from decimal import Decimal

from schemas.models import MasterConstraint

SAFE_DECIMAL_MIN = Decimal("-999999999999.99999999")
SAFE_DECIMAL_MAX = Decimal("999999999999.99999999")


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
        # ==========================
        # DECIMAL / PERCENT
        # ==========================
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
            "min_decimal": SAFE_DECIMAL_MIN,
            "max_decimal": SAFE_DECIMAL_MAX,
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
            "applies_to": MasterConstraint.AppliesTo.DECIMAL,
            "default_decimal": None,
            "min_decimal": SAFE_DECIMAL_MIN,
            "max_decimal": SAFE_DECIMAL_MAX,
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
