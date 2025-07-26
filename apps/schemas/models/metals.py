from django.core.exceptions import ValidationError
from django.db import models
from assets.models.metals import PreciousMetalHolding
from .base import Schema, SchemaColumn, SchemaColumnValue


class MetalPortfolioSchema(Schema):
    relation_name = 'metal_schema'
    metal_portfolio = models.ForeignKey(
        'portfolios.MetalPortfolio',
        on_delete=models.CASCADE,
        related_name='schemas'
    )

    class Meta:
        unique_together = (('metal_portfolio', 'name'))

    @property
    def portfolio_relation_name(self):
        return 'metal_portfolio'


class MetalPortfolioSC(SchemaColumn):
    ASSET_TYPE = 'metal'

    schema = models.ForeignKey(
        MetalPortfolioSchema,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    source_field = models.CharField(
        max_length=100,
        blank=True
    )

    class Meta:
        unique_together = (('schema', 'title'))

    def __str__(self):
        return f"[{self.schema.metal_portfolio.portfolio.profile}] {self.title} ({self.source})"

    def get_holdings_for_column(self):
        from assets.models.metals import PreciousMetalHolding
        return PreciousMetalHolding.objects.filter(
            storage_facility__metal_portfolio=self.schema.metal_portfolio
        )


class MetalPortfolioSCV(SchemaColumnValue):
    column = models.ForeignKey(
        MetalPortfolioSC,
        on_delete=models.CASCADE,
        related_name='values'
    )
    holding = models.ForeignKey(
        PreciousMetalHolding,
        on_delete=models.CASCADE,
        related_name='column_values'
    )

    class Meta:
        unique_together = (('column', 'holding'),)

    def get_portfolio_from_column(self):
        return self.column.schema.metal_portfolio

    def get_portfolio_from_holding(self):
        return self.holding.storage_facility.metal_portfolio
