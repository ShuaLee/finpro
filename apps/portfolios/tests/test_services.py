"""
Tests for Portfolio Services
----------------------------
Includes tests for stock dashboard aggregation logic.
"""

from django.test import TestCase
from users.models import User, Profile
from portfolios.models import Portfolio, StockPortfolio
from portfolios.services.stock_dashboard_service import get_stock_dashboard


class StockDashboardServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="stocktest@example.com", password="pass")
        self.profile = Profile.objects.get(user=self.user)
        self.portfolio = Portfolio.objects.create(profile=self.profile)
        self.stock_portfolio = StockPortfolio.objects.create(portfolio=self.portfolio)

    def test_dashboard_empty_portfolio_returns_zeroes(self):
        dashboard = get_stock_dashboard(self.stock_portfolio)
        self.assertEqual(dashboard["total_self_managed_value_fx"], 0)
        self.assertEqual(dashboard["total_managed_value_fx"], 0)
        self.assertEqual(dashboard["total_combined_value_fx"], 0)
        self.assertIsInstance(dashboard["self_managed_accounts"], list)
        self.assertIsInstance(dashboard["managed_accounts"], list)