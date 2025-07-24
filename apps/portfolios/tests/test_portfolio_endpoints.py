"""
Tests for Portfolio Endpoints
-----------------------------

Covers:
- POST /api/v1/portfolios/
- GET  /api/v1/portfolios/me/
"""

from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Profile
from portfolios.models import Portfolio
import pytest


@pytest.mark.django_db
class TestPortfolioEndpoints:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123")
        self.profile = Profile.objects.create(user=self.user)
        self.create_url = reverse("create-portfolio")
        self.detail_url = reverse("portfolio-detail")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_portfolio_success(self):
        """Authenticated user can create a portfolio if none exists."""
        self.authenticate()
        response = self.client.post(self.create_url)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert "profile" in data
        assert "created_at" in data
        assert data["stock_portfolio"] is None
        assert data["metal_portfolio"] is None
        assert Portfolio.objects.count() == 1

    def test_create_portfolio_twice_should_fail(self):
        """Creating a portfolio twice returns 400 error."""
        self.authenticate()
        Portfolio.objects.create(profile=self.profile)
        response = self.client.post(self.create_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[
            "error"] == "Portfolio already exists for this user."

    def test_get_portfolio_success(self):
        """Retrieve an existing portfolio for authenticated user."""
        self.authenticate()
        portfolio = Portfolio.objects.create(profile=self.profile)
        response = self.client.get(self.detail_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == portfolio.id
        assert data["profile"] == self.profile.id
        assert "created_at" in data

    def test_get_portfolio_not_found(self):
        """Returns 404 if no portfolio exists for the user."""
        self.authenticate()
        response = self.client.get(self.detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"] == "Portfolio not found."

    def test_unauthenticated_access(self):
        """Endpoints should require authentication."""
        response = self.client.post(self.create_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = self.client.get(self.detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
