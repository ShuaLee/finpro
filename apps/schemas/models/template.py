from django.db import models


class SchemaTemplate(models.Model):
    """
    A global blueprint defining the default schema for a specific account type.
    Used when initializing new portfolio-level Schemas.
    """
    account_type = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Account type this template applies to (e.g., equity_self, crypto_wallet)."
    )
    name = models.CharField(
        max_length=100, help_text="Human-readable template name.")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["account_type"]

    def __str__(self):
        return f"{self.name} ({self.account_type})"


class SchemaTemplateColumn(models.Model):
    """
    Defines a column inside a SchemaTemplate.
    These columns are copied into SchemaColumn instances when a schema is initialized.
    """
    template = models.ForeignKey(
        SchemaTemplate,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    title = models.CharField(max_length=255)
    identifier = models.SlugField(max_length=100, db_index=True)

    # Data behavior
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

    source = models.CharField(
        max_length=20,
        choices=[
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("formula", "Formula"),
            ("custom", "Custom"),
        ],
    )
    source_field = models.CharField(max_length=100, null=True, blank=True)

    # UI & logic flags
    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    # Defines if columns are auto-included in new schemas
    is_default = models.BooleanField(
        default=False,
        help_text="If True, this column will appear automatically when a schema is generated."
    )

    display_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("template", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.template.account_type})"
