from django.core.exceptions import ValidationError
from django.db import models


class AllocationPlan(models.Model):
    """
    A target allocation strategy for a portfolio.
    """

    class BaseScope(models.TextChoices):
        TOTAL_PORTFOLIO = "total_portfolio", "Total Portfolio"
        ACCOUNT_TYPE = "account_type", "Single Account Type"

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="allocation_plans",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    base_value_identifier = models.SlugField(
        max_length=100,
        default="total_value_profile_ccy",
        help_text="SCV identifier used as the base value for allocation math.",
    )

    base_scope = models.CharField(
        max_length=30,
        choices=BaseScope.choices,
        default=BaseScope.TOTAL_PORTFOLIO,
    )

    account_type = models.ForeignKey(
        "accounts.AccountType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocation_plans",
        help_text="Required only when base_scope=account_type.",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "name"],
                name="uniq_allocation_plan_name_per_portfolio",
            )
        ]
        ordering = ["name"]

    def clean(self):
        super().clean()

        if self.base_scope == self.BaseScope.ACCOUNT_TYPE and not self.account_type:
            raise ValidationError("account_type is required when base_scope='account_type'.")

        if self.base_scope != self.BaseScope.ACCOUNT_TYPE and self.account_type_id:
            raise ValidationError("account_type must be empty unless base_scope='account_type'.")

    def __str__(self):
        return f"{self.portfolio_id}:{self.name}"


class AllocationScenario(models.Model):
    """
    Versioned scenario under a plan (e.g. base, aggressive, defensive).
    """

    plan = models.ForeignKey(
        AllocationPlan,
        on_delete=models.CASCADE,
        related_name="scenarios",
    )

    name = models.SlugField(max_length=100)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "name"],
                name="uniq_allocation_scenario_name_per_plan",
            ),
            models.UniqueConstraint(
                fields=["plan"],
                condition=models.Q(is_default=True),
                name="uniq_default_allocation_scenario_per_plan",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.plan.name}:{self.name}"
