from django.db import models

class Analytic(models.Model):
    """
    Top-level analytic definition for a portfolio.
    Example: "Country Exposure", "Asset Class Breakdown".
    """

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="analytics",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    # SCV identifier to sum, usually total_value_profile_ccy
    value_identifier = models.SlugField(
        max_length=100,
        default="total_value_profile_ccy",
    )

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

    def __str__(self):
        return f"{self.portfolio_id}:{self.name}"
