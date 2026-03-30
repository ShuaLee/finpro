import uuid
from django.db import models
from django.utils.text import slugify

from fx.models.country import Country


class Exchange(models.Model):
    """
    Reference stock exchange sourced from FMP.

    Characteristics:
    - Provider-owned
    - Immutable reference data
    - Safe to truncate & rebuild
    - Shared across all equities
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Short code: NASDAQ, NYSE, LSE, JPX
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
    )

    # Human-readable name
    name = models.CharField(max_length=255)

    slug = models.SlugField(
        unique=True,
        blank=True,
        db_index=True,
    )

    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="exchanges",
    )

    # Provider metadata
    symbol_suffix = models.CharField(max_length=20, null=True, blank=True)
    delay = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.name})"
