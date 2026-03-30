from django.core.exceptions import ValidationError
from django.db import models


class Analytic(models.Model):
    """
    Portfolio-scoped analytic definition.
    """

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="analytics",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    # Schema identifier whose numeric value is aggregated.
    value_identifier = models.SlugField(max_length=100, default="current_value")

    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "name"],
                name="uniq_analytic_name_per_portfolio",
            )
        ]
        ordering = ["name"]
        indexes = [models.Index(fields=["portfolio", "is_active"]) ]

    def clean(self):
        super().clean()

        if self.pk:
            original = Analytic.objects.only("portfolio_id", "is_system").filter(pk=self.pk).first()
            if original and original.portfolio_id != self.portfolio_id:
                raise ValidationError("Analytic portfolio cannot be changed.")
            if original and original.is_system and not self.is_system:
                raise ValidationError("System analytics cannot be converted to custom analytics.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System analytics cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio_id}:{self.name}"
