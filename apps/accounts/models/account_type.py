from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Value
from django.utils.text import slugify

from assets.models.core import AssetType


class AccountType(models.Model):
    name = models.CharField(max_length=100)

    slug = models.SlugField(
        max_length=50,
        blank=True,
        null=True,
        help_text="System identifier (only for system-defined account types).",
    )

    is_system = models.BooleanField(default=False)

    owner = models.ForeignKey(
        "users.Profile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="custom_account_types",
    )

    allowed_asset_types = models.ManyToManyField(
        AssetType,
        blank=True,
        related_name="account_types",
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            # Enforce namespace-level name uniqueness
            models.UniqueConstraint(
                fields=["name", "owner"],
                condition=Q(is_system=False),
                name="uniq_user_accounttype_name",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(is_system=True),
                name="uniq_system_accounttype_name",
            ),
            models.CheckConstraint(
                condition=Q(is_system=True, owner__isnull=True)
                | Q(is_system=False, owner__isnull=False),
                name="accounttype_owner_required_if_not_system",
            ),
        ]

    # -------------------------------------------------
    # Validation (THIS blocks the bug you hit)
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if self.is_system and self.owner is not None:
            raise ValidationError("System account types cannot have an owner.")

        if not self.is_system and self.owner is None:
            raise ValidationError(
                "User-defined account types must have an owner.")

        if not self.is_system:
            if AccountType.objects.filter(
                is_system=True,
                name__iexact=self.name,
            ).exists():
                raise ValidationError(
                    f"'{self.name}' is a reserved system account type name."
                )

    # -------------------------------------------------
    # Save logic
    # -------------------------------------------------

    def save(self, *args, **kwargs):
        if self.is_system:
            if not self.slug:
                self.slug = slugify(self.name)
        else:
            self.slug = None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
