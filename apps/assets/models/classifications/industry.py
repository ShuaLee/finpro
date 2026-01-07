import uuid

from django.db import models
from django.utils.text import slugify


class Industry(models.Model):
    """
    Industry classification sourced from FMP.

    - System-only reference data
    - Users may override via SchemaColumnValues (SCVs)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Human-readable industry name (e.g., 'Semiconductors').",
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="URL-safe unique slug.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # SAVE LOGIC
    # -------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
