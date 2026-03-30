from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from profiles.models import Profile


class AssetType(models.Model):
    """
    Defines the category / behaviour of an Asset.

    - System asset types: created_by = NULL, immutable
    - User asset types: scoped to a user, editable name
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, editable=False)

    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asset_types",
        help_text="Null = system-defined asset type",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            # System namespace uniqueness
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(created_by__isnull=True),
                name="unique_system_asset_type_name",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=Q(created_by__isnull=True),
                name="unique_system_asset_type_slug",
            ),
            # User namespace uniqueness
            models.UniqueConstraint(
                fields=["created_by", "name"],
                condition=Q(created_by__isnull=False),
                name="unique_asset_type_name_per_user",
            ),
            models.UniqueConstraint(
                fields=["created_by", "slug"],
                condition=Q(created_by__isnull=False),
                name="unique_asset_type_slug_per_user",
            ),
        ]

    # -------------------------
    # Validation & lifecycle
    # -------------------------
    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()

        if not self.name:
            raise ValidationError("Asset type name is required.")

        queryset = AssetType.objects.exclude(pk=self.pk)

        # Prevent user asset types from colliding with system ones
        if self.created_by:
            if queryset.filter(
                created_by__isnull=True,
                name__iexact=self.name,
            ).exists():
                raise ValidationError(
                    f"'{self.name}' is reserved for system asset type."
                )
            if queryset.filter(
                created_by=self.created_by,
                name__iexact=self.name,
            ).exists():
                raise ValidationError(
                    "You already have an asset type with this name."
                )
            if self.slug and queryset.filter(
                created_by=self.created_by,
                slug__iexact=self.slug,
            ).exists():
                raise ValidationError(
                    "You already have an asset type with this slug."
                )
        else:
            if queryset.filter(
                created_by__isnull=True,
                name__iexact=self.name,
            ).exists():
                raise ValidationError(
                    "System asset type name must be unique."
                )
            if self.slug and queryset.filter(
                created_by__isnull=True,
                slug__iexact=self.slug,
            ).exists():
                raise ValidationError(
                    "System asset type slug must be unique."
                )

        # Prevent mutating system asset types.
        if self.pk:
            old = AssetType.objects.get(pk=self.pk)
            if old.created_by is None:
                if self.name != old.name:
                    raise ValidationError(
                        "System asset types cannot be renamed."
                    )
                if self.slug != old.slug:
                    raise ValidationError(
                        "System asset type slugs cannot be changed manually."
                    )
                if self.created_by_id is not None:
                    raise ValidationError(
                        "System asset types cannot be reassigned."
                    )

    def save(self, *args, **kwargs):
        # System types use canonical code-safe slugs.
        system_slug_overrides = {
            "Equity": "equity",
            "Cryptocurrency": "crypto",
            "Commodity": "commodity",
            "Precious Metal": "precious_metal",
            "Real Estate": "real_estate",
        }

        if self.created_by is None and self.name in system_slug_overrides:
            self.slug = system_slug_overrides[self.name]
        elif not self.slug:
            self.slug = slugify(self.name)
        elif self.pk and self.created_by_id is not None:
            previous = AssetType.objects.get(pk=self.pk)
            if self.name != previous.name:
                self.slug = slugify(self.name)

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.created_by is None:
            raise ValidationError("System asset types are immutable.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
