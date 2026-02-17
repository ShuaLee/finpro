"""
Main Portfolio Model
--------------------

Represents a portfolio container for a profile's investments.

Responsibilities:
- Links to a user's `Profile` (one-to-many).
- Supports both personal and client portfolio tracking.

Business Rules:
- Exactly one `is_main=True` portfolio per profile.
"""

from django.core.exceptions import ValidationError
from django.db import models

from profiles.models import Profile


class Portfolio(models.Model):
    """
    Represents a portfolio linked to a user's profile.

    Attributes:
        profile (ForeignKey): A profile can have multiple portfolios.
        created_at (DateTime): Timestamp when the portfolio is created.
    """

    class Kind(models.TextChoices):
        PERSONAL = "personal", "Personal"
        CLIENT = "client", "Client"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="portfolios",
    )
    name = models.CharField(max_length=100, default="Main Portfolio")
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.PERSONAL,
    )
    client_name = models.CharField(max_length=150, null=True, blank=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["profile", "kind"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(is_main=True),
                name="unique_main_portfolio_per_profile",
            ),
            models.UniqueConstraint(
                fields=["profile", "name"],
                name="unique_portfolio_name_prt_profile",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(kind=Kind.PERSONAL, client_name__isnull=True)
                    | models.Q(kind=Kind.PERSONAL, client_name="")
                    | (
                        models.Q(kind=Kind.CLIENT, client_name__isnull=False)
                        & ~models.Q(client_name="")
                    )
                ),
                name="client_name_required_for_client_portfolio",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(is_main=False)
                    | (
                        models.Q(is_main=True, kind=Kind.PERSONAL)
                        & (
                            models.Q(client_name__isnull=True)
                            | models.Q(client_name="")
                        )
                    )
                ),
                name="main_portfolio_must_be_personal",
            ),
        ]

    def __str__(self):
        if self.kind == self.Kind.CLIENT and self.client_name:
            return f"{self.profile.user.email} - {self.name} ({self.client_name})"
        return f"{self.profile.user.email} - {self.name}"

    def clean(self):
        if self.is_main and self.kind != self.Kind.PERSONAL:
            raise ValidationError("Main portfolio must be a personal portfolio.")

        if self.is_main and self.client_name:
            raise ValidationError("Main portfolio cannot have a client name.")

        if self.pk and not self.is_main:
            has_other_main = Portfolio.objects.filter(
                profile=self.profile,
                is_main=True,
            ).exclude(pk=self.pk).exists()
            if not has_other_main:
                raise ValidationError("Each profile must always have a main portfolio.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_main:
            raise ValidationError("Main portfolio cannot be deleted.")
        return super().delete(*args, **kwargs)
