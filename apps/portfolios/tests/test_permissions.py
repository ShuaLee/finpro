"""
Tests for Custom Permissions
----------------------------
Ensure only the owner can view/edit their portfolios.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User, Profile
from portfolios.models import Portfolio, StockPortfolio


class PortfolioPermissionsTests(APITestCase):
    def setUp(self):
        # User A
        self.user_a = User.objects.create_user(email="owner@example.com", password="pass")
        self.profile_a = Profile.objects.get(user=self.user_a)
        self.portfolio_a = Portfolio.objects.create(profile=self.profile_a)
        self.stock_a = StockPortfolio.objects.create(portfolio=self.portfolio_a)

        # User B
        self.user_b = User.objects.create_user(email="intruder@example.com", password="pass")
        self.profile_b = Profile.objects.get(user=self.user_b)
        self.portfolio_b = Portfolio.objects.create(profile=self.profile_b)
        self.stock_b = StockPortfolio.objects.create(portfolio=self.portfolio_b)

        self.url_dashboard = reverse('stock-portfolio-dashboard')

    def test_owner_can_access_dashboard(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url_dashboard)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_access_dashboard(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.url_dashboard)
        # Should still 404 because view looks up by request.user.profile
        # But custom permission check ensures correct behavior if object passed
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)