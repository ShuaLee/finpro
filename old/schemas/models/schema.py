from django.core.exceptions import ValidationError
from django.db import models

from schemas.services.formulas.resolver import FormulaDependencyResolver


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

    # Field name OR unused (depending on source)
    source_field = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Required for asset/holding sources."
    )

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

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    def clean(self):
        super().clean()

        # ---- Source consistency rules ----

        if self.source == "formula":
            if not self.formula:
                raise ValidationError(
                    "Columns with source='formula' must define a formula."
                )
            if self.source_field:
                raise ValidationError(
                    "source_field must be empty when source='formula'."
                )

        elif self.source in ("asset", "holding"):
            if not self.source_field:
                raise ValidationError(
                    f"Columns with source='{self.source}' require source_field."
                )
            if self.formula:
                raise ValidationError(
                    "formula must be empty unless source='formula'."
                )

        elif self.source == "custom":
            if self.source_field or self.formula:
                raise ValidationError(
                    "Custom columns cannot define source_field or formula."
                )

        else:
            raise ValidationError(f"Invalid source '{self.source}'.")

    # -------------------------------------------------
    # Save / immutability
    # -------------------------------------------------
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            old = SchemaColumn.objects.get(pk=self.pk)
            immutable_fields = ["data_type", "source"]

            if old.source != "formula":
                immutable_fields.append("formula")

            for field in immutable_fields:
                if getattr(old, field) != getattr(self, field):
                    raise ValidationError(
                        f"Field '{field}' cannot be changed after creation."
                    )

        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------------------------------
    # Delete behavior
    # -------------------------------------------------
    def delete(self, *args, **kwargs):
        if not self.is_deletable:
            raise ValidationError(
                f"Column '{self.title}' cannot be deleted — it is system-protected."
            )

        # -------------------------------------------------
        # Prevent deletion if required by any formula column
        # -------------------------------------------------
        for formula_col in self.schema.columns.filter(
            source="formula",
            formula__isnull=False,
        ):
            resolver = FormulaDependencyResolver(formula_col.formula)
            if self.identifier in resolver.extract_identifiers():
                raise ValidationError(
                    f"Column '{self.title}' is required by calculated column "
                    f"'{formula_col.title}' and cannot be deleted."
                )

        schema = self.schema
        removed_order = self.display_order

        super().delete(*args, **kwargs)

        schema.columns.filter(
            display_order__gt=removed_order
        ).update(
            display_order=models.F("display_order") - 1
        )



class SchemaColumnValue(models.Model):
    """
    Stores the actual value for a given column + holding.
    Example: Quantity = 10, Price = 100.
    """

    SOURCE_SYSTEM = "system"
    SOURCE_FORMULA = "formula"
    SOURCE_USER = "user"

    SOURCE_CHOICES = (
        (SOURCE_SYSTEM, "System"),
        (SOURCE_FORMULA, "Formula"),
        (SOURCE_USER, "User Override"),
    )

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

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_SYSTEM,
        db_index=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("column", "holding")

    def __str__(self):
        return f"{self.column.identifier} = {self.value} ({self.source})"
