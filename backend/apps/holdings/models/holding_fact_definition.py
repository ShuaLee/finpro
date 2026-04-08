from django.core.exceptions import ValidationError
from django.db import models

from apps.holdings.constants import BUILTIN_HOLDING_VALUE_KEYS, HOLDING_VALUE_TYPE_CHOICES


class HoldingFactDefinition(models.Model):
    portfolio = models.ForeignKey(
        "holdings.Portfolio",
        on_delete=models.CASCADE,
        related_name="holding_fact_definitions",
    )
    key = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, choices=HOLDING_VALUE_TYPE_CHOICES, default="string")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["label", "key"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "key"],
                name="uniq_holding_fact_definition_per_portfolio",
            ),
        ]
        indexes = [
            models.Index(fields=["portfolio", "is_active"]),
        ]

    def clean(self):
        super().clean()
        self.label = (self.label or "").strip()
        self.description = (self.description or "").strip()
        self.key = (self.key or "").strip().lower()

        if not self.label:
            raise ValidationError({"label": "Label is required."})
        if self.key in BUILTIN_HOLDING_VALUE_KEYS:
            raise ValidationError({"key": "This key is reserved by the system."})

        if self.pk:
            previous = HoldingFactDefinition.objects.only("portfolio_id").filter(pk=self.pk).first()
            if previous and previous.portfolio_id != self.portfolio_id:
                raise ValidationError("Fact definition portfolio cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio.name}:{self.key}"
