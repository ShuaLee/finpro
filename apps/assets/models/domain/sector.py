import uuid

from django.db import models
from django.utils.text import slugify

class Sector(models.Model):
    """
    Market sector classification.
    Supports:
    - System sectors (from FMP)
    - User-created sectors (private to the user)   
    """
    id = models.UUIDField(primary_key=True, default=uuid.uid4, editable=False)

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

    class Meta:
        constraints = [
            # Enforce uniqueness in separate namespaces
            models.UniqueConstraint(
                fields=["slug", "owner"],
                name="unique_sector_slug_per_owner"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name