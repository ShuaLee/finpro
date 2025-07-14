from django.core.exceptions import ValidationError
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

    @property
    def portfolio_relation_name(self):
        return 'stock_portfolio'


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

    def get_holdings_for_column(self):
        from assets.models.stocks import StockHolding
        return StockHolding.objects.filter(
            self_managed_account__stock_portfolio=self.schema.stock_portfolio
        )

    def __str__(self):
        return f"[{self.schema.stock_portfolio.portfolio.profile}] {self.title} ({self.source})"


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

    def get_portfolio_from_column(self):
        return self.column.schema.stock_portfolio

    def get_portfolio_from_holding(self):
        return self.holding.self_managed_account.stock_portfolio
