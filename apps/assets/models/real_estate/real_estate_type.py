from django.db import models
from django.core.exceptions import ValidationError

from users.models.profile import Profile


class RealEstateType(models.Model):
    """
    Classification for real estate assets.

    - System types are predefined by the app
    - Users may create private custom types
    - User-defined types are NOT shared
    """

    name = models.CharField(max_length=100)

    description = models.TextField(
        blank=True,
        help_text="Optional description or clarification."
    )

    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="real_estate_types",
        help_text="NULL = system type; otherwise user-owned."
    )

    class Meta:
        constraints = [
            # System types: unique globally
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(created_by__isnull=True),
                name="uniq_system_real_estate_type",
            ),

            # User types: unique per user
            models.UniqueConstraint(
                fields=["name", "created_by"],
                condition=models.Q(created_by__isnull=False),
                name="uniq_user_real_estate_type",
            ),
        ]

        ordering = ["name"]

    def clean(self):
        super().clean()

        # Prevent user from duplicating a system-defined type
        if self.created_by and RealEstateType.objects.filter(
            name=self.name,
            created_by__isnull=True,
        ).exists():
            raise ValidationError(
                f"'{self.name}' is a system-defined property type."
            )

    @property
    def is_system(self) -> bool:
        return self.created_by is None

    def __str__(self):
        return self.name
