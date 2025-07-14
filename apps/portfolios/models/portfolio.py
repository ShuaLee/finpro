from django.db import models
from users.models import Profile


class Portfolio(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    profile_setup_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile} - {self.created_at}"

    def initialize_stock_portfolio(self):
        from portfolios.models.stocks import StockPortfolio
        from schemas.constants import DEFAULT_STOCK_SCHEMA_COLUMNS
        from schemas.models.stocks import StockPortfolioSchema, StockPortfolioSC

        if hasattr(self, 'stockportfolio'):
            return  # Already exists

        stock_portfolio = StockPortfolio.objects.create(portfolio=self)

        schema = StockPortfolioSchema.objects.create(
            stock_portfolio=stock_portfolio,
            name=f"Default Schema for {stock_portfolio}"
        )

        for column_data in DEFAULT_STOCK_SCHEMA_COLUMNS:
            StockPortfolioSC.objects.create(schema=schema, **column_data)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.initialize_stock_portfolio()