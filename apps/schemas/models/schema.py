from django.core.exceptions import ValidationError
from django.db import models


class Schema(models.Model):
    """
    Universal schema definition for a given account_type.
    Example: Stock Self-Managed Schema vs Stock Managed Schema.
    Shared across all accounts of the same type.
    """
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="schemas"
    )

    account_type = models.ForeignKey(
        "accounts.AccountType",
        on_delete=models.CASCADE,
        related_name="schemas",
        help_text="AccountType this schema applies to.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One schema per account_type per portfolio
        unique_together = ("portfolio", "account_type")
        ordering = ["account_type__slug"]

    def __str__(self):
        return f"{self.portfolio} — {self.account_type.name} Schema"


class SchemaColumn(models.Model):
    """
    Defines a column inside a Schema.
    """

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    title = models.CharField(max_length=255)
    identifier = models.SlugField(max_length=100, db_index=True)

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

    # field name OR formula identifier
    source_field = models.CharField(max_length=100, null=True, blank=True)

    # Formula FK (nullable)
    formula = models.ForeignKey(
        "schemas.Formula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="columns",
    )

    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("schema", "identifier")
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.title} ({self.schema.account_type.slug})"

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            old = SchemaColumn.objects.get(pk=self.pk)
            immutable = ["data_type", "source", "source_field", "formula"]

            for field in immutable:
                if getattr(old, field) != getattr(self, field):
                    raise ValidationError(
                        f"Field '{field}' cannot be changed after creation."
                    )

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self.is_deletable:
            raise ValidationError(
                f"Column '{self.title}' cannot be deleted — it's system-protected."
            )

        schema = self.schema
        removed_order = self.display_order

        super().delete(*args, **kwargs)

        schema.columns.filter(display_order__gt=removed_order).update(
            display_order=models.F("display_order") - 1
        )


class SchemaColumnValue(models.Model):
    """
    Stores the actual value for a given column + holding.
    Example: Quantity = 10, Price = 100.
    """

    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="values",
    )
    holding = models.ForeignKey(
        "accounts.Holding",
        on_delete=models.CASCADE,
        related_name="schema_values",
    )

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ("column", "holding")

    def __str__(self):
        return f"{self.column.title} = {self.value} ({self.holding})"
