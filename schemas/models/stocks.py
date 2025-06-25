from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from .base import Schema, SchemaColumn, SchemaColumnValue


class StockPortfolioSchema(Schema):
    stock_portfolio = models.ForeignKey(
        'portfolios.StockPortfolio',
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
        blank=True
    )

    class Meta:
        unique_together = (('schema', 'title'),)

    def __str__(self):
        return f"[{self.schema.stock_portfolio.portfolio.profile}] {self.title} ({self.source})"

    def save(self, *args, **kwargs):
        # this lazy import needs to be fixed
        from assets.models.stocks import StockHolding
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
        'assets.StockHolding',
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
