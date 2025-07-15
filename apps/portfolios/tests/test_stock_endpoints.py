from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User, Profile
from portfolios.models import Portfolio, StockPortfolio

class StockPortfolioEndpointTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="stockuser@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        self.profile = Profile.objects.get(user=self.user)
        self.portfolio = Portfolio.objects.create(profile=self.profile)

    def test_create_stock_portfolio_success(self):
        url = reverse('create-stock-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StockPortfolio.objects.filter(portfolio=self.portfolio).exists())

    def test_create_stock_portfolio_twice_should_fail(self):
        StockPortfolio.objects.create(portfolio=self.portfolio)
        url = reverse('create-stock-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stock_dashboard_not_found_without_stock_portfolio(self):
        url = reverse('stock-portfolio-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stock_dashboard_with_empty_stock_portfolio(self):
        StockPortfolio.objects.create(portfolio=self.portfolio)
        url = reverse('stock-portfolio-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check keys in dashboard response
        for key in ["total_self_managed_value_fx", "total_managed_value_fx", "total_combined_value_fx"]:
            self.assertIn(key, response.data)