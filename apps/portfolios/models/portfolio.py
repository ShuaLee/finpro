"""
Main Portfolio Model
--------------------

Represents a portfolio container for a profile's investments.

Responsibilities:
- Links to a user's `Profile` (one-to-many).
- Supports both personal and client portfolio tracking.

Business Rules:
- Exactly one personal portfolio per profile.
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["profile", "kind"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(kind="personal"),
                name="unique_personal_portfolio_per_profile",
            ),
            models.UniqueConstraint(
                fields=["profile", "name"],
                name="unique_portfolio_name_prt_profile",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind="personal", client_name__isnull=True)
                    | models.Q(kind="personal", client_name="")
                    | (
                        models.Q(kind="client", client_name__isnull=False)
                        & ~models.Q(client_name="")
                    )
                ),
                name="client_name_required_for_client_portfolio",
            ),
        ]

    def __str__(self):
        if self.kind == self.Kind.CLIENT and self.client_name:
            return f"{self.profile.user.email} - {self.name} ({self.client_name})"
        return f"{self.profile.user.email} - {self.name}"

    def clean(self):
        super().clean()

        if self.pk:
            original = Portfolio.objects.only(
                "profile_id",
                "kind",
                "name",
                "client_name",
            ).filter(pk=self.pk).first()
            if original and original.profile_id != self.profile_id:
                raise ValidationError("Portfolio owner cannot be changed.")
            if original and original.kind == self.Kind.PERSONAL:
                if self.kind != original.kind:
                    raise ValidationError("Personal portfolio kind cannot be changed.")
                if self.name != original.name:
                    raise ValidationError("Personal portfolio name cannot be changed.")
                if (self.client_name or "") != (original.client_name or ""):
                    raise ValidationError("Personal portfolio client_name cannot be changed.")

        if self.kind == self.Kind.PERSONAL and self.client_name:
            raise ValidationError("Personal portfolio cannot have a client name.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.kind == self.Kind.PERSONAL:
            raise ValidationError("Personal portfolio cannot be deleted.")
        return super().delete(*args, **kwargs)
