from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class AssetType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, editable=False)
    created_by = models.ForeignKey(
        "users.Profile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asset_types",
        help_text="Null means a common system asset type.",
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(created_by__isnull=True),
                name="uniq_system_asset_type_name",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=Q(created_by__isnull=True),
                name="uniq_system_asset_type_slug",
            ),
            models.UniqueConstraint(
                fields=["created_by", "name"],
                condition=Q(created_by__isnull=False),
                name="uniq_user_asset_type_name",
            ),
            models.UniqueConstraint(
                fields=["created_by", "slug"],
                condition=Q(created_by__isnull=False),
                name="uniq_user_asset_type_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["created_by", "name"]),
        ]

    @property
    def is_system(self) -> bool:
        return self.created_by is None

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.description = (self.description or "").strip()

        if not self.name:
            raise ValidationError("Asset type name is required.")

        reserved_slug = slugify(self.name).replace("-", "_")
        queryset = AssetType.objects.exclude(pk=self.pk)

        if self.created_by is None:
            if queryset.filter(created_by__isnull=True, name__iexact=self.name).exists():
                raise ValidationError("System asset type name must be unique.")
        else:
            if queryset.filter(created_by__isnull=True, name__iexact=self.name).exists():
                raise ValidationError(
                    f"'{self.name}' is reserved by a system asset type.")
            if queryset.filter(created_by=self.created_by, name__iexact=self.name).exists():
                raise ValidationError(
                    "You already have an asset type with this name.")
            if queryset.filter(created_by=self.created_by, slug=reserved_slug).exists():
                raise ValidationError(
                    "You already have an asset type with this slug.")

        if self.pk:
            previous = AssetType.objects.filter(pk=self.pk).first()
            if previous and previous.is_system:
                if self.created_by is not None:
                    raise ValidationError(
                        "System asset types cannot be reassigned.")
                if self.name != previous.name:
                    raise ValidationError(
                        "System asset types cannot be renamed.")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name).replace("-", "_")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System asset types cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
