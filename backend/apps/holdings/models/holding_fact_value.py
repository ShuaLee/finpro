from django.core.exceptions import ValidationError
from django.db import models


class HoldingFactValue(models.Model):
    holding = models.ForeignKey(
        "holdings.Holding",
        on_delete=models.CASCADE,
        related_name="fact_values",
    )
    definition = models.ForeignKey(
        "holdings.HoldingFactDefinition",
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["definition__label", "definition__key", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["holding", "definition"],
                name="uniq_holding_fact_value_per_definition",
            ),
        ]
        indexes = [
            models.Index(fields=["holding", "definition"]),
        ]

    def clean(self):
        super().clean()
        if self.holding_id and self.definition_id:
            if self.holding.container.portfolio_id != self.definition.portfolio_id:
                raise ValidationError(
                    "Fact value definition must belong to the same portfolio as the holding."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.holding_id}:{self.definition.key}"
