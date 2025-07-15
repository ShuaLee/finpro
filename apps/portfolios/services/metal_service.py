"""
Metal Portfolio Service
-----------------------

This module provides services for creating and managing MetalPortfolio objects.
All business logic related to metal-specific portfolios is centralized here.

Responsibilities:
- Create a MetalPortfolio under an existing Portfolio.
- Validate uniqueness to ensure only one MetalPortfolio exists per Portfolio.
"""

from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from portfolios.models.metal import MetalPortfolio


def create_metal_portfolio(portfolio: Portfolio) -> MetalPortfolio:
    """
    Creates a MetalPortfolio for the given Portfolio.

    Args:
        portfolio (Portfolio): The main portfolio instance.

    Returns:
        MetalPortfolio: The newly created MetalPortfolio instance.

    Raises:
        ValidationError: If the portfolio already has a MetalPortfolio.
    """
    if hasattr(portfolio, "metal_portfolio"):
        raise ValidationError(
            "MetalPortfolio already exists for this portfolio.")

    metal_portfolio = MetalPortfolio.objects.create(portfolio=portfolio)
    return metal_portfolio
