import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

class Industry(models.Model):
    """
    Industry classification (e.g., 'Semiconductors', 'Oil & Gas Midstream').

    - System industries come from FMP (is_system=True, owner=None)
    - Users may create private custom industries (owner=user)
    - Slugs are unique per owner (global for system industries)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=150,
        help_text="Human-readable industry name (e.g., 'Semiconductors')."
    )

    slug = models.SlugField(
        max_length=150,
        help_text="URL-safe unique slug (e.g., 'semiconductors')."
    )

    # System seed = owner = NULL
    # User custom industry = owner = user
    owner = models.ForeignKey(
        'users.Profile',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="custom_industries",
        help_text="NULL for system industries. Set to user for custom industries.",
    )

    is_system = models.BooleanField(
        default=False,
        help_text="True if this industry comes from FMP and is global for all users.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # CLEAN + SAVE OVERRIDES
    # -------------------------
    def clean(self):
        super().clean()

        # System industries must not have an owner
        if self.is_system and self.owner is not None:
            raise ValidationError(
                "System industries (is_system=True) cannot have an owner."
            )
        
        # Custom industries must NOT be marked as system
        if self.owner and self.is_system:
            raise ValidationError(
                "User-created industries cannot be marked as system."
            )
        
        def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.name)

            self.clean()
            return super().save(*args, **kwargs)
        
        class Meta:
            constraints = [
            # System industries: slug must be globally unique
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(owner__isnull=True),
                name="unique_system_industry_slug",
            ),
            # Custom industries: slug must be unique per owner
            models.UniqueConstraint(
                fields=["slug", "owner"],
                condition=models.Q(owner__isnull=False),
                name="unique_user_industry_slug_per_owner",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name