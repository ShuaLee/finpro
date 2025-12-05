from django.db import models


class SchemaTemplate(models.Model):
    """
    A global blueprint defining the default schema for a specific AccountType.
    Used when initializing new portfolio-level Schemas.
    """

    account_type = models.OneToOneField(   # unique FK → OneToOneField is correct
        "accounts.AccountType",
        on_delete=models.CASCADE,
        related_name="schema_template",
        db_index=True,
        help_text="AccountType this template applies to.",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["account_type__slug"]

    def __str__(self):
        return f"{self.name} ({self.account_type.slug})"


class SchemaTemplateColumn(models.Model):

    template = models.ForeignKey(
        SchemaTemplate,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    title = models.CharField(max_length=255)
    identifier = models.SlugField(max_length=100, db_index=True)

    # Data type
    data_type = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("decimal", "Decimal"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("boolean", "Boolean"),
            ("url", "URL"),
        ],
    )

    # Source of the column value
    source = models.CharField(
        max_length=20,
        choices=[
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("formula", "Formula"),
            ("custom", "Custom"),
        ],
    )

    # NEW — proper FK to Formula (required by admin UI)
    formula = models.ForeignKey(
        "schemas.Formula",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="template_columns",
        help_text="Formula to use when source='formula'."
    )

    # String-based field for asset/holding/custom source fields
    # (ignored if source='formula')
    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Holding/Asset field name OR unused when formula is provided."
    )

    constraints = models.JSONField(default=dict, blank=True)

    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("template", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.template.account_type.slug})"
