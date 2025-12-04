from django.core.exceptions import ValidationError
from django.db import models

from users.models.profile import Profile


class RealEstateType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="custom_property_types",
    )

    class Meta:
        unique_together = ("name", "created_by")  # important

    def clean(self):
        super().clean()

        # If this is a user-created type (not system)
        if not self.is_system:
            # Check if a system type exists with the same name
            if RealEstateType.objects.filter(name=self.name, is_system=True).exists():
                raise ValidationError(
                    f"'{self.name}' is a system-defined property type and cannot be duplicated."
                )

    def __str__(self):
        return self.name
