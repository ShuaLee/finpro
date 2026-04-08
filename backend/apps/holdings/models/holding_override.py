from django.core.exceptions import ValidationError
from django.db import models

from apps.holdings.constants import HOLDING_VALUE_TYPE_CHOICES


class HoldingOverride(models.Model):
    holding = models.ForeignKey(
        "holdings.Holding",
        on_delete=models.CASCADE,
        related_name="overrides",
    )
    key = models.SlugField(max_length=100)
    data_type = models.CharField(max_length=20, choices=HOLDING_VALUE_TYPE_CHOICES, default="string")
    value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["holding", "key"],
                name="uniq_holding_override_per_key",
            ),
        ]
        indexes = [
            models.Index(fields=["holding", "key"]),
        ]

    def clean(self):
        super().clean()
        self.key = (self.key or "").strip().lower()
        if not self.key:
            raise ValidationError({"key": "Key is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.holding_id}:{self.key}"
