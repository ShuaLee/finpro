from django.apps import AppConfig


class StockPortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_portfolio'

    def ready(self):
        import stock_portfolio.signals
