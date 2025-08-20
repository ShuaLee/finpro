from django.db import models
from portfolios.models.custom import CustomPortfolio
from accounts.models.base import BaseAccount

class CustomAccount(BaseAccount):
    """
    An account container inside a CustomPortfolio (e.g. 'Pokemon Cards', 'Garage', etc.)
    """
    custom_portfolio = models.ForeignKey(
        CustomPortfolio,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    asset_type = "custom"
    account_variant = "custom_account"

    class Meta:
        verbose_name = "Custom Account"
        constraints = [
            models.UniqueConstraint(
                fields=['custom_portfolio', 'name'],
                name='unique_customaccount_name_in_customportfolio'
            )
        ]

    @property
    def sub_portfolio(self):
        return self.custom_portfolio
    
    @property
    def active_schema(self):
        # Return the Schema object for this portfolio + account model
        return self.custom_portfolio.get_schema_for_account_model(type(self))
    