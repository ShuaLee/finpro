from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from assets.constants import ASSET_SCHEMA_CONFIG
from assets.models import StockHolding
from stock_portfolio.models import StockPortfolio
import logging

logger = logging.getLogger(__name__)

# ----------------------------- Abstract Classes ------------------------------ #


class Schema(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class SchemaColumn(models.Model):
    DATA_TYPES = [
        ('decimal', 'Number'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ]
    SOURCE_TYPE = [
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ]

    @classmethod
    def get_source_field_choices(cls):
        asset_type = getattr(cls, 'ASSET_TYPE', None)
        if not asset_type:
            return []

        config = ASSET_SCHEMA_CONFIG.get(asset_type, {})
        choices = []
        for source, fields in config.items():
            for source_field in fields:
                label = f"{source} - {source_field.replace('_', ' ').title()}" if source_field else f"{source} - Custom"
                choices.append((source_field, label))
        return choices

    title = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100, blank=True, null=True)
    decimal_spaces = models.PositiveSmallIntegerField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} ({self.source})"

    def clean(self):
        if self.source in ['asset', 'holding'] and not self.source_field:
            raise ValidationError(
                "source_field is required for asset or holding sources.")

        # Dynamically validate source_field against ASSET_SCHEMA_CONFIG
        asset_type = getattr(self.__class__, 'ASSET_TYPE', None)

        if not asset_type:
            raise ValidationError(
                "ASSET_TYPE must be defined on the SchemaColumn subclass.")

        if self.source not in ['asset', 'holding', 'calculated'] or not asset_type:
            return  # Skip further validation

        source_config = ASSET_SCHEMA_CONFIG.get(
            asset_type, {}).get(self.source, {})
        valid_fields = list(source_config.keys())

        if self.source_field not in valid_fields:
            raise ValidationError(
                f"Invalid source_field '{self.source_field}' for source '{self.source}' "
                f"in asset type '{asset_type}'. Valid options: {sorted(valid_fields)}"
            )

    def delete(self, *args, **kwargs):
        if not self.is_deletable:
            raise PermissionDenied(
                "This column is mandatory and cannot be deleted.")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        asset_type = getattr(self.__class__, 'ASSET_TYPE', None)

        if asset_type and self.source_field and self.source in ['asset', 'holding', 'calculated']:
            field_config = ASSET_SCHEMA_CONFIG.get(asset_type, {}).get(
                self.source, {}).get(self.source_field)
            if field_config:
                # Auto-set values from config if not manually specified
                self.data_type = field_config.get('data_type', self.data_type)
                if 'editable' in field_config:
                    self.editable = field_config['editable']

                if hasattr(self, 'decimal_spaces') and 'decimal_spaces' in field_config:
                    self.decimal_spaces = field_config['decimal_spaces']

                if not self.title:
                    self.title = self.source_field.replace('_', ' ').title()

        self.full_clean()
        super().save(*args, **kwargs)


class SchemaColumnValue(models.Model):
    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def clean(self):
        # Only validate type if this is an override
        if self.is_edited and self.value is not None:
            expected_type = self.column.data_type
            try:
                if expected_type == 'decimal':
                    float(self.value)
                elif expected_type == 'string':
                    str(self.value)
                elif expected_type == 'integer':
                    int(self.value)
                # Optionally: add handling for 'date', 'url'
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Invalid type for '{self.column.title}'. Expected {expected_type}."
                )

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.is_edited and self.value is not None:
            try:
                data_type = self.column.data_type
                places = self.column.decimal_spaces or 2

                if data_type == 'decimal':
                    val = round(float(self.value), places)
                elif data_type == 'integer':
                    val = int(self.value)
                elif data_type == 'string':
                    val = str(self.value)
                else:
                    val = self.value  # fallback raw

                self.value = str(val)  # Store consistently as text

            except (TypeError, ValueError):
                raise ValidationError(
                    f"Invalid value for '{self.column.title}'")

        # Apply directly to holding if column targets holding field
        if self.column.source == 'holding' and self.value:
            if hasattr(self.holding, self.column.source_field):
                setattr(self.holding, self.column.source_field,
                        float(self.value))
                self.holding.save()

            # Clear override — the value was applied directly to the model
            self.value = None
            self.is_edited = False

        super().save(*args, **kwargs)

    def get_value(self):
        """
        Return the user-edited value or the derived value.
        """
        if self.is_edited:
            return self.value

        # Logic to derive value based on column's source
        column = self.column

        if column.source == 'asset':
            # Fetch from asset (e.g., stock price)
            return getattr(self.holding.asset, column.source_field, None)
        elif column.source == 'holding':
            # Fetch from holding (e.g., quantity)
            return getattr(self.holding, column.source_field, None)

        return None


# ------------------------------ Stock Portfolio ------------------------------ #


class StockPortfolioSchema(Schema):
    stock_portfolio = models.ForeignKey(
        StockPortfolio,
        on_delete=models.CASCADE,
        related_name='schemas'
    )

    class Meta:
        unique_together = (('stock_portfolio', 'name'))

    def delete(self, *args, **kwargs):
        if self.stock_portfolio.schemas.count() <= 1:
            raise PermissionDenied(
                "Cannot delete the last schema for a Stock Portfolio.")
        super().delete(*args, **kwargs)


class StockPortfolioSC(SchemaColumn):
    ASSET_TYPE = 'stock'

    schema = models.ForeignKey(
        StockPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    source_field = models.CharField(
        max_length=100,
        choices=SchemaColumn.get_source_field_choices.__func__(),
        blank=True
    )

    class Meta:
        unique_together = (('schema', 'title'),)

    def __str__(self):
        return f"[{self.schema.stock_portfolio.portfolio.profile}] {self.title} ({self.source})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create column values for all holdings on new column creation
        if is_new:
            holdings = StockHolding.objects.filter(
                self_managed_account__stock_portfolio=self.schema.stock_portfolio
            )
            for holding in holdings:
                StockPortfolioSCV.objects.get_or_create(
                    column=self,
                    holding=holding
                )


class StockPortfolioSCV(SchemaColumnValue):
    column = models.ForeignKey(
        StockPortfolioSC,
        on_delete=models.CASCADE,
        related_name='values'
    )
    holding = models.ForeignKey(
        StockHolding,
        on_delete=models.CASCADE,
        related_name='column_values'
    )

    class Meta:
        unique_together = (('column', 'holding'),)

    def clean(self):
        if self.column and self.holding:
            if self.holding.self_managed_account.stock_portfolio != self.column.schema.stock_portfolio:
                raise ValidationError(
                    "Mismatched portfolio between column and holding.")

    super().clean()  # ← Run the base class validation
