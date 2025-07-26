from django.db import models
from .base import Schema, SchemaColumn, SchemaColumnValue


class StockPortfolioSchema(Schema):
    relation_name = 'stock_portfolio'
    stock_portfolio = models.ForeignKey(
        'portfolios.StockPortfolio',
        on_delete=models.CASCADE,
        related_name='schemas'
    )

    class Meta:
        unique_together = (('stock_portfolio', 'name'),)

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

    class Meta:
        unique_together = (('schema', 'title'),)


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
