from django.core.exceptions import ValidationError
from django.db import models
from core.countries import validate_country_code



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

    all_countries = models.BooleanField(
        default=False,
        help_text="If true, this classification applies globally (all countries)."
    )
    jurisdictions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of ISO country codes (e.g., ['US'], ['CA'], ['GB'])."
    )

    is_system = models.BooleanField(
        default=True,
        help_text="True if this is a built-in classification available globally."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        if self.all_countries:
            return f"{self.name} ({self.tax_status}, All Countries)"
        countries = ", ".join(self.jurisdictions) if self.jurisdictions else "N/A"
        return f"{self.name} ({self.tax_status}, {countries})"

    def clean(self):
        """
        Validation: either all_countries is true OR jurisdictions must be valid.
        """
        if self.all_countries:
            self.jurisdictions = []  # clear it to avoid conflicts
        else:
            for code in self.jurisdictions:
                try:
                    validate_country_code(code)
                except ValueError as e:
                    raise ValidationError(str(e))


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
        ordering = ["definition__name",]

    def __str__(self):
        return f"{self.definition.name} ({self.profile.user.email})"
