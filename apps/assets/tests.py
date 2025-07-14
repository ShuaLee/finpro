from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from accounts.models.stocks import SelfManagedAccount
from assets.models.stocks import Stock
from external_data.fmp.dispatch import fetch_asset_data
from external_data.fmp.stocks import apply_fmp_stock_data
from decimal import Decimal
from unittest.mock import patch


User = get_user_model()


class FMPIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="Helpome123",
            first_name="Test",
            last_name="User",
            birth_date="2000-01-01"
        )
        self.profile = self.user.profile
        self.portfolio = self.profile.portfolio
        self.account = SelfManagedAccount.objects.create(
            name="Test Account", stock_portfolio=self.portfolio.stockportfolio
        )
    
    @patch("external_data.fmp.dispatch.fetch_stock_data")
    def test_create_stock_and_not_custom(self, mock_fetch):
        mock_fetch.return_value = {
            "quote": {"price": 100.0},
            "profile": {"name": "Test Co", "currency": "USD"}
        }
        stock = Stock(ticker="AAPL")
        success = fetch_asset_data(stock, "stock", verify_custom=True)
        self.assertTrue(success)
        self.assertEqual(stock.ticker, "AAPL")
        self.assertEqual(stock.is_custom, False)
        self.assertEqual(stock.price, Decimal("100.0000"))

    @patch("external_data.fmp.stocks.fetch_stock_data")
    def test_create_custom_stock_on_failure(self, mock_fetch):
        mock_fetch.return_value = None
        stock = Stock(ticker="FAKE123")
        success = fetch_asset_data(stock, "stock", verify_custom=True)
        self.assertFalse(success)
        self.assertTrue(stock.is_custom)

    def test_apply_fmp_stock_data_calculates_dividend_yield(self):
        stock = Stock(ticker="DIVD")
        quote = {"price": 50}
        profile = {"lastDiv": 0.50, "currency": "USD"}
        success = apply_fmp_stock_data(stock, quote, profile)
        self.assertTrue(success)
        self.assertAlmostEqual(float(stock.dividend_yield), 0.04, places=4)

    def test_fxrate_gets_applied_correctly(self):
        from users.models import FXRate
        from external_data.fx import get_fx_rate

        FXRate.objects.create(
            from_currency="USD",
            to_currency="CAD",
            rate=1.25,
            updated_at=timezone.now()
        )
        rate = get_fx_rate("USD", "CAD")
        self.assertEqual(rate, 1.25)

    def test_fxrate_self_conversion_returns_1(self):
        from external_data.fx import get_fx_rate
        rate = get_fx_rate("USD", "USD")
        self.assertEqual(rate, 1.0)
