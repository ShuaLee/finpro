"""
Tests for Portfolio Endpoints
-----------------------------

Covers:
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
        # User creation triggers Profile + Portfolio creation
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.detail_url = reverse("portfolio-detail")
        self.create_url = reverse("create-portfolio")  # Optional legacy endpoint

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_auto_portfolio_exists_after_user_creation(self):
        """Ensure portfolio is auto-created when user is created."""
        profile = Profile.objects.get(user=self.user)
        portfolio = Portfolio.objects.filter(profile=profile).first()
        assert portfolio is not None

    def test_get_portfolio_success(self):
        """Authenticated user should retrieve their portfolio."""
        self.authenticate()
        response = self.client.get(self.detail_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["profile"] == Profile.objects.get(user=self.user).id

    def test_post_create_portfolio_should_fail(self):
        """
        If a user tries to create a portfolio manually,
        API should return 400 since it's auto-created.
        """
        self.authenticate()
        response = self.client.post(self.create_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Portfolio already exists" in str(response.json())

    def test_unauthenticated_access_is_denied(self):
        """Endpoints should require authentication."""
        response = self.client.get(self.detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
