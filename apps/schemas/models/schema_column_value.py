from django.db import models


class SchemaColumnValue(models.Model):
    """
    Stores the computed or user-overridden value
    for a SchemaColumn and Holding.
    """

    class Source(models.TextChoices):
        SYSTEM = "system", "System"
        FORMULA = "formula", "Formula"
        USER = "user", "User Override"

    column = models.ForeignKey(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="values",
    )

    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.CASCADE,
        related_name="schema_values",
    )

    value = models.TextField(
        null=True,
        blank=True,
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.SYSTEM,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("column", "holding")

    # --------------------------------------------------
    # String representation (SAFE)
    # --------------------------------------------------
    def __str__(self):
        # Never leak raw values via __str__
        return f"{self.column.identifier} [{self.get_source_display()}]"

    # --------------------------------------------------
    # Explicit accessors
    # --------------------------------------------------
    @property
    def canonical_value(self):
        """
        Canonical stored value.

        ✔ Safe for:
          - services
          - formula evaluation
          - recomputation

        ❌ NEVER use for display.
        """
        return self.value

    @property
    def display_value(self):
        from schemas.services.queries import SchemaQueryService
        return SchemaQueryService.display_value_for_scv(self)
