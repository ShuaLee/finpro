from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from users.models.profile import Profile


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
            # Same user cannot create duplicate names
            models.UniqueConstraint(
                fields=["created_by", "name"],
                name="unique_asset_type_name_per_user",
            ),
            # Same user cannot create suplicate slugs
            models.UniqueConstraint(
                fields=["created_by", "slug"],
                name="unique_asset_Type_slug_per_user",
            ),
        ]

    # -------------------------
    # Validation & lifecycle
    # -------------------------
    def clean(self):
        super().clean()

        # Prevent user asset types from colldiing with system ones
        if self.created_by:
            if AssetType.objects.filter(
                created_by__isnull=True,
                name__iexact=self.name,
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f"'{self.name}' is reserved for system asset type."
                )

        # Prevent renaming system asset types
        if self.pk:
            old = AssetType.objects.get(pk=self.pk)
            if old.created_by is None:
                if self.name != old.name:
                    raise ValidationError(
                        "System asset types cannot be renamed."
                    )

    def save(self, *args, **kwargs):
        # Auto-generate slug from name
        if not self.slug or (
            self.pk
            and self.created_by is not None
            and self.name != AssetType.objects.get(pk=self.pk).name
        ):
            self.slug = slugify(self.name)

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.created_by is None:
            raise ValidationError("System asset types are immutable.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
