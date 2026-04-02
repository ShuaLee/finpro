from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Holding(models.Model):
    container = models.ForeignKey(
        "holdings.Container",
        on_delete=models.CASCADE,
        related_name="holdings",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    quantity = models.DecimalField(
        max_digits=40,
        decimal_places=18,
        default=Decimal("1"),
        help_text="Number of units held. Use 1 for directly valued holdings when appropriate.",
    )
    unit_value = models.DecimalField(
        max_digits=40,
        decimal_places=18,
        null=True,
        blank=True,
        help_text="Current value per unit for this holding.",
    )
    unit_cost_basis = models.DecimalField(
        max_digits=40,
        decimal_places=18,
        null=True,
        blank=True,
        help_text="Optional cost basis per unit.",
    )

    notes = models.TextField(blank=True)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible holding-specific metadata and overrides.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["container", "asset", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["container", "asset"],
                name="uniq_holding_per_container_asset",
            ),
        ]
        indexes = [
            models.Index(fields=["container", "asset"]),
            models.Index(fields=["asset"]),
        ]

    @property
    def current_value(self):
        quantity = self.quantity
        unit_value = self.unit_value

        if quantity is None or unit_value is None:
            return None
        return quantity * unit_value

    @property
    def invested_value(self):
        quantity = self.quantity
        unit_cost_basis = self.unit_cost_basis

        if quantity is None or unit_cost_basis is None:
            return None
        return quantity * unit_cost_basis

    def clean(self):
        super().clean()

        self.notes = (self.notes or "").strip()

        if self.quantity <= 0:
            raise ValidationError(
                {"quantity": "Quantity must be greater than zero."})

        if self.unit_value is not None and self.unit_value < 0:
            raise ValidationError(
                {"unit_value": "Unit value cannot be negative."})

        if self.unit_cost_basis is not None and self.unit_cost_basis < 0:
            raise ValidationError(
                {"unit_cost_basis": "Unit cost basis cannot be negative."}
            )

        if self.pk:
            previous = (
                Holding.objects
                .select_related("container", "asset")
                .filter(pk=self.pk)
                .first()
            )
            if previous and previous.container.pk != self.container.pk:
                raise ValidationError("Holding container cannot be changed.")
            if previous and previous.asset.pk != self.asset.pk:
                raise ValidationError("Holding asset cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset} in {self.container.name}"
