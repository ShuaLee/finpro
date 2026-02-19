from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from assets.models.core import AssetType
from formulas.models.formula import Formula


class DependencyPolicy(models.TextChoices):
    AUTO_EXPAND = "auto_expand", "Auto-expand dependencies"
    STRICT = "strict", "Strict (no auto-create)"


class FormulaDefinition(models.Model):
    """
    Semantic definition of a formula in a given context.

    Example:
        identifier = "current_value"
        asset_type = equity
        formula = quantity * price

    Notes:
    - Meaning lives here
    - Schema existence DOES NOT live here
    """

    owner = models.ForeignKey(
        "profiles.Profile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="formula_definitions",
        help_text="Null = system definition, otherwise user-owned."
    )

    identifier = models.SlugField(
        max_length=100,
        help_text="Semantic identifier (e.g. current_value)."
    )

    name = models.CharField(
        max_length=100,
        help_text="Display name."
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description of this formula's meaning."
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.CASCADE,
        related_name="formula_definitions",
    )

    formula = models.ForeignKey(
        Formula,
        on_delete=models.PROTECT,
        related_name="definitions",
    )

    dependency_policy = models.CharField(
        max_length=20,
        choices=DependencyPolicy.choices,
        default=DependencyPolicy.STRICT,
        help_text="How missing dependencies are handled."
    )

    is_system = models.BooleanField(
        default=False,
        help_text="System-defined and analytics-safe."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]
        constraints = [
            models.UniqueConstraint(
                fields=["identifier", "asset_type", "owner"],
                name="uniq_formula_definition_per_asset_type_owner"
            )
        ]

    def clean(self):
        super().clean()

        if not self.identifier:
            raise ValidationError("Identifier is required.")

        if self.is_system and self.owner_id is not None:
            raise ValidationError("System definitions cannot have an owner.")

        if not self.is_system and self.owner_id is None:
            raise ValidationError("User definitions must have an owner.")

        if self.formula_id is None:
            raise ValidationError("formula is required.")

        if self.owner_id is not None:
            if self.formula.owner_id not in (None, self.owner_id):
                raise ValidationError(
                    "You can only use system formulas or formulas you own."
                )

        if self.pk:
            previous = FormulaDefinition.objects.filter(pk=self.pk).first()
            if previous and previous.is_system:
                immutable_fields = (
                    "owner_id",
                    "identifier",
                    "asset_type_id",
                    "formula_id",
                    "dependency_policy",
                    "is_system",
                )
                for field in immutable_fields:
                    if getattr(self, field) != getattr(previous, field):
                        raise ValidationError(
                            f"System definition field '{field}' cannot be changed."
                        )

    def save(self, *args, **kwargs):
        self.identifier = slugify(self.identifier).replace("-", "_")
        if self.owner_id is None:
            self.is_system = True
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System formula definitions cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        scope = "system" if self.owner is None else f"user={self.owner_id}"
        return f"{self.identifier} [{self.asset_type.slug}] ({scope})"
