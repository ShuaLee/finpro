from django.db import models


class ThemeDefinition(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    category = models.CharField(
        max_length=20,
        choices=[
            ("system", "System-defined"),
            ("custom", "User-defined"),
        ]
    )

    """
    When calculating exposure:
    Do we sum quantity? current_value? purchase_value? custom_column?
    """

    weight_column = models.CharField(
        max_length=100,
        default="current_value",
        help_text="Which SchemaColumn identifier to use for weighting."
    )


class ThemeRule(models.Model):
    """
    Example Theme: Country Exposure

    Name: Country Exposure

    weight_column: "current_value"

    Rules:

    column_identifier = "country", operator=eq, value = "Canada"

    column_identifier = "country", operator=eq, value = "USA"

    column_identifier = "country", operator=eq, value = "Argentina"
    """
    theme = models.ForeignKey(
        ThemeDefinition,
        related_name="rules",
        on_delete=models.CASCADE
    )

    # Which SchemaColumn to check?
    column_identifier = models.CharField(max_length=100)

    operator = models.CharField(max_length=20, choices=[
        ("eq", "Equals"),
        ("neq", "Not Equals"),
        ("contains", "Contains"),
        ("in", "In Set"),
        ("gt", ">"),
        ("lt", "<"),
    ])

    # Compare to what?
    value = models.CharField(max_length=255)
