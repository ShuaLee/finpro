from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from portfolios.models import StockPortfolio
import pytest


@pytest.mark.django_db
class TestStockPortfolioEndpoints:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )
        self.url = reverse("create-stock-portfolio")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_stock_portfolio_success(self):
        """
        Authenticated user should successfully create a StockPortfolio.
        """
        self.authenticate()
        response = self.client.post(self.url)
        assert response.status_code == status.HTTP_201_CREATED

        # Check response fields
        data = response.json()
        assert "id" in data
        assert "portfolio" in data
        assert StockPortfolio.objects.count() == 1

    def test_duplicate_stock_portfolio_should_fail(self):
        """
        Second creation attempt should return 400 error.
        """
        self.authenticate()
        # First creation
        self.client.post(self.url)
        # Second attempt
        response = self.client.post(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "StockPortfolio already exists" in str(response.json())

    def test_unauthenticated_access_is_denied(self):
        """
        Unauthenticated users should receive 401 Unauthorized.
        """
        response = self.client.post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
