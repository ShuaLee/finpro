from django.db import models


class SchemaTemplate(models.Model):
    """
    Defines a reusable schema blueprint for an account type.
    """

    identifier = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Stable system identifier (e.g. equity_default)."
    )

    name = models.CharField(
        max_length=255,
        help_text="Human-readable template name."
    )

    account_type = models.ForeignKey(
        "accounts.AccountType",
        on_delete=models.CASCADE,
        related_name="schema_templates",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template can be used for generation."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["account_type__slug", "identifier"]

    def __str__(self):
        return f"{self.name} ({self.account_type.slug})"


class SchemaColumnTemplate(models.Model):
    """
    Blueprint for a SchemaColumn.
    """

    template = models.ForeignKey(
        SchemaTemplate,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    title = models.CharField(max_length=255)

    identifier = models.SlugField(
        max_length=100,
        help_text="Must match formula dependency identifiers if formula-based."
    )

    data_type = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("decimal", "Decimal"),
            ("integer", "Integer"),
            ("boolean", "Boolean"),
            ("date", "Date"),
        ],
    )

    source = models.CharField(
        max_length=20,
        choices=[
            ("holding", "Holding"),
            ("asset", "Asset"),
            ("formula", "Formula"),
        ],
    )

    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Attribute path for holding/asset OR formula identifier."
    )

    formula_definition = models.ForeignKey(
        "formulas.FormulaDefinition",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="template_columns",
    )

    constraints = models.JSONField(
        default=dict,
        blank=True,
        help_text="Constraint overrides."
    )

    is_default = models.BooleanField(
        default=True,
        help_text="Added automatically on schema creation."
    )

    is_system = models.BooleanField(
        default=True,
        help_text="System-managed column."
    )

    is_editable = models.BooleanField(default=False)
    is_deletable = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        unique_together = ("template", "identifier")

    def __str__(self):
        return f"{self.title} ({self.template.identifier})"
