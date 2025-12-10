import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from fx.models.country import Country
from users.models.profile import Profile


class Exchange(models.Model):
    """
    Represents a stock exchange from FMP's /available-exchanges endpoint.
    All records are system-managed (is_system=True).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Short code: "NASDAQ", "NYSE", "LSE", "JPX"
    code = models.CharField(max_length=20, unique=True, db_index=True)

    # Human-readable name: "London Stock Exchange", "Tokyo Stock Exchange"
    name = models.CharField(max_length=255)

    # Automatically generated from code for convenience
    slug = models.SlugField(unique=True, blank=True)

    # Country relationship
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="exchanges",
    )

    # New: FMP metadata
    symbol_suffix = models.CharField(max_length=20, null=True, blank=True)
    delay = models.CharField(max_length=50, null=True, blank=True)

    # System flag
    is_system = models.BooleanField(default=True, editable=False)

    # (optional for future functionality)
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If null → system exchange; If set → user-created exchange."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------------
    # VALIDATION
    # ---------------------------------
    def clean(self):
        super().clean()

        if self.is_system and self.owner is not None:
            raise ValidationError("System exchanges cannot have an owner.")

        if self.owner and self.is_system:
            raise ValidationError(
                "User-created exchanges cannot be system exchanges.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)

        self.clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            # System exchanges → code must be globally unique
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(owner__isnull=True),
                name="unique_system_exchange_code",
            ),

            # User-created exchanges → unique per user
            models.UniqueConstraint(
                fields=["code", "owner"],
                condition=models.Q(owner__isnull=False),
                name="unique_user_exchange_code_per_owner",
            ),
        ]

        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.name})"
