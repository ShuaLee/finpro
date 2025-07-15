from django.test import TestCase
from users.models import User
from portfolios.models import Portfolio, StockPortfolio
from accounts.services import stock_account_service

class StockAccountServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="servicetest@example.com", password="pass")
        self.portfolio = Portfolio.objects.create(profile=self.user.profile)
        self.stock_portfolio = StockPortfolio.objects.create(portfolio=self.portfolio)

    def test_create_self_managed_account(self):
        account = stock_account_service.create_self_managed_account(self.user, {"name": "Service Account"})
        self.assertEqual(account.name, "Service Account")