from django.db import models


class ConstraintType(models.Model):
    """
    Describes a type of constraint that can be applied to a DataType.

    Examples:
        - max_length (string, url)
        - min_value (decimal)
        - max_value (decimal)
        - decimal_places (decimal)
        - regex (string, url)
    """
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    applies_to = models.ManyToManyField(
        "datatype.DataType",
        related_name="allowed_constraint_types",
        blank=True,
    )

    value_data_type = models.ForeignKey(
        "datatype.DataType",
        on_delete=models.PROTECT,
        related_name="constraint_value_types",
        null=True,
        blank=True,
    )

    is_system = models.BooleanField(default=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.slug


class ConstraintDefinition(models.Model):
    """
    System-level default constraint values for a given DataType + ConstraintType.

    Example:
      DataType('decimal') + ConstraintType('decimal_places') → default = 2
      DataType('string') + ConstraintType('max_length') → default = 255

    These do NOT apply directly to columns or assets — those are AppliedConstraints.
    """
    data_type = models.ForeignKey(
        "datatype.DataType",
        on_delete=models.CASCADE,
        related_name="default_constraints",
    )

    constraint_type = models.ForeignKey(
        "datatype.ConstraintType",
        on_delete=models.CASCADE,
        related_name="default_definitions",
    )

    default_value = models.TextField(
        null=True,
        blank=True,
        help_text="System-level default value for this constraint."
    )

    allow_user_override = models.BooleanField(
        default=False,
        help_text="Whether user or custom assets can override this constraint."
    )

    is_system = models.BooleanField(default=True)

    class Meta:
        unique_together = ("data_type", "constraint_type")
        ordering = ["data_type__slug", "constraint_type__slug"]

    def __str__(self):
        return f"{self.data_type.slug} → {self.constraint_type.slug} = {self.default_value}"


class AppliedConstraint(models.Model):
    """
    A specific constraint applied to a schema column.

    Examples:
    - decimal_places = "8"
    - max_value = "1000000"
    - max_length = "50"
    """
    schema_column = models.ForeignKey(
        "schemas.SchemaColumn",
        on_delete=models.CASCADE,
        related_name="applied_constraints",
    )

    constraint_type = models.ForeignKey(
        "datatype.ConstraintType",
        on_delete=models.CASCADE,
        related_name="applied_constraints",
    )

    value = models.TextField()

    is_user_defined = models.BooleanField(default=False)

    class Meta:
        unique_together = ("schema_column", "constraint_type")

    def __str__(self):
        return f"{self.schema_column.identifier} → {self.constraint_type.slug} = {self.value}"
