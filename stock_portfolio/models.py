from django.db import models

class StockPortfolio(models.Model):
    portfolio = models.OneToOneField('portfolio.Portfolio', on_delete=models.CASCADE, related_name='stock_portfolio')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"