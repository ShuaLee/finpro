from django.db import models
from django.core.exceptions import ValidationError

from profiles.models import Profile


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
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError("Property type name is required.")

        queryset = RealEstateType.objects.exclude(pk=self.pk)

        # Prevent user from duplicating a system-defined type
        if self.created_by:
            if queryset.filter(
                name__iexact=self.name,
                created_by__isnull=True,
            ).exists():
                raise ValidationError(
                    f"'{self.name}' is a system-defined property type."
                )
            if queryset.filter(
                name__iexact=self.name,
                created_by=self.created_by,
            ).exists():
                raise ValidationError(
                    "You already have a property type with this name."
                )
        elif queryset.filter(
            name__iexact=self.name,
            created_by__isnull=True,
        ).exists():
            raise ValidationError("System property type name must be unique.")

        if self.pk:
            old = RealEstateType.objects.get(pk=self.pk)
            if old.created_by is None:
                if self.name != old.name:
                    raise ValidationError("System property types cannot be renamed.")
                if self.created_by_id is not None:
                    raise ValidationError("System property types cannot be reassigned.")

    @property
    def is_system(self) -> bool:
        return self.created_by is None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.created_by is None:
            raise ValidationError("System property types are immutable.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
