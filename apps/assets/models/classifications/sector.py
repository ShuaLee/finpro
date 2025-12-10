import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Sector(models.Model):
    """
    Market sector classification.
    Supports:
    - System sectors (from FMP)
    - User-created sectors (private to the user)   
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, db_index=True)

    # System vs custom
    is_system = models.BooleanField(default=False)

    # Null for system sectors; filled for custom sectors
    owner = models.ForeignKey(
        'users.Profile',
        on_delete=models.CASCADE,
        related_name="custom_sectors",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------
    # VALIDATION
    # ------------------------
    def clean(self):
        super().clean()

        # System sectors must not have an owner
        if self.is_system and self.owner is not None:
            raise ValidationError(
                "System sectors (is_system=True) cannot have an owner."
            )

    # ------------------------
    # SAVE LOGIC
    # ------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        self.clean()
        return super().save(*args, **kwargs)

    # ------------------------
    # UNIQUE CONSTRAINTS
    # ------------------------
    class Meta:
        constraints = [
            # System sectors: slug must be globally unique
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(owner__isnull=True),
                name="unique_system_sector_slug",
            ),
            # Custom sectors: slug must be unique per owner
            models.UniqueConstraint(
                fields=["slug", "owner"],
                condition=models.Q(owner__isnull=False),
                name="unique_user_sector_slug_per_owner",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name
