from django.db import models


class ClassificationDefinition(models.Model):
    """
    Global system-level account classification definitions.
    Shared across all users (e.g., TFSA, RRSP, 401k, Taxable).
    """

    name = models.CharField(max_length=100, unique=True)  # e.g. "TFSA", "401k"
    tax_status = models.CharField(
        max_length=50,
        choices=[
            ("taxable", "Taxable"),
            ("tax_deferred", "Tax-Deferred"),
            ("tax_exempt", "Tax-Exempt"),
        ],
        default="taxable",
    )
    jurisdiction = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Jurisdiction where this classification applies (e.g., Canada, US, UK)."
    )
    is_system = models.BooleanField(
        default=True,
        help_text="True if this is a built-in classification available globally."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.tax_status})"


class AccountClassification(models.Model):
    """
    User-specific classification instance.
    References a global definition but stores user-level state
    like contribution room and carry forward amounts.
    """

    profile = models.ForeignKey(
        "users.Profile",
        on_delete=models.CASCADE,
        related_name="account_classifications",
    )
    definition = models.ForeignKey(
        ClassificationDefinition,
        on_delete=models.CASCADE,
        related_name="instances",
    )
    nickname = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional nickname for this classification (e.g., 'Vacation TFSA')."
    )

    # User-specific tax contribution tracking
    contribution_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual contribution limit for this user (if applicable)."
    )
    carry_forward_room = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unused contribution room carried forward."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "definition")
        ordering = ["nickname", "definition__name"]

    def __str__(self):
        label = self.nickname or self.definition.name
        return f"{label} ({self.profile.user.email})"
