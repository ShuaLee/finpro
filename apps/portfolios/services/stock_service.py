from django.db import transaction
from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from portfolios.models.stock import StockPortfolio
from schemas.services.schema_initialization import initialize_stock_schemas_for_portfolio


@transaction.atomic
def create_stock_portfolio(portfolio: Portfolio) -> StockPortfolio:
    if hasattr(portfolio, "stockportfolio"):
        raise ValidationError(
            "StockPortfolio already exists for this portfolio.")

    # Insert allowed now because FKs are nullable
    stock_portfolio = StockPortfolio.objects.create(portfolio=portfolio)

    # Create both schemas and attach
    sm_schema, m_schema = initialize_stock_schemas_for_portfolio(
        stock_portfolio)

    StockPortfolio.objects.filter(pk=stock_portfolio.pk).update(
        self_managed_schema=sm_schema,
        managed_schema=m_schema,
    )

    stock_portfolio.refresh_from_db(
        fields=["self_managed_schema", "managed_schema"])
    return stock_portfolio
