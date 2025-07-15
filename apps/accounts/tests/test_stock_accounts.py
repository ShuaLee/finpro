from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User
from portfolios.models import Portfolio, StockPortfolio
from accounts.models import SelfManagedAccount, ManagedAccount

class StockAccountTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="teststock@example.com", password="pass")
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(profile=self.user.profile)
        self.stock_portfolio = StockPortfolio.objects.create(portfolio=self.portfolio)

    def test_create_self_managed_account(self):
        url = reverse('self-managed-accounts')
        data = {"name": "My Account", "broker": "Robinhood", "tax_status": "taxable", "account_type": "individual"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SelfManagedAccount.objects.count(), 1)

    def test_list_self_managed_accounts(self):
        SelfManagedAccount.objects.create(stock_portfolio=self.stock_portfolio, name="Account1")
        url = reverse('self-managed-accounts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_managed_account(self):
        url = reverse('managed-accounts')
        data = {
            "name": "Managed 1", "broker": "IBKR", "tax_status": "taxable",
            "account_type": "individual", "strategy": "growth",
            "invested_amount": "1000.00", "current_value": "1100.00"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ManagedAccount.objects.count(), 1)

    def test_stock_dashboard(self):
        SelfManagedAccount.objects.create(stock_portfolio=self.stock_portfolio, name="Account1")
        ManagedAccount.objects.create(stock_portfolio=self.stock_portfolio, name="Managed", invested_amount=1000, current_value=1200)
        url = reverse('stock-accounts-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("combined_total_fx", response.data)
