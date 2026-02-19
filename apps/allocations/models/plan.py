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
        default="current_value",
        help_text="Schema identifier used as the base value for allocation math.",
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
        indexes = [models.Index(fields=["portfolio", "is_active"]) ]

    def clean(self):
        super().clean()

        if self.base_scope == self.BaseScope.ACCOUNT_TYPE and not self.account_type:
            raise ValidationError("account_type is required when base_scope='account_type'.")

        if self.base_scope != self.BaseScope.ACCOUNT_TYPE and self.account_type_id:
            raise ValidationError("account_type must be empty unless base_scope='account_type'.")

        if self.account_type and self.account_type.owner_id and self.account_type.owner_id != self.portfolio.profile_id:
            raise ValidationError("Custom account_type must belong to the same profile as this portfolio.")

        if self.pk:
            original = AllocationPlan.objects.only("portfolio_id").filter(pk=self.pk).first()
            if original and original.portfolio_id != self.portfolio_id:
                raise ValidationError("Allocation plan portfolio cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
            )
        ]
        ordering = ["name"]
        indexes = [models.Index(fields=["plan", "is_active"]) ]

    def clean(self):
        super().clean()
        if self.is_default:
            qs = AllocationScenario.objects.filter(plan=self.plan, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one default scenario is allowed per plan.")

        if self.pk:
            original = AllocationScenario.objects.only("plan_id").filter(pk=self.pk).first()
            if original and original.plan_id != self.plan_id:
                raise ValidationError("Allocation scenario plan cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plan.name}:{self.name}"
