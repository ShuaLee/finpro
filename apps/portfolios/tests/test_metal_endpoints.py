from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User, Profile
from portfolios.models import Portfolio, MetalPortfolio

class MetalPortfolioEndpointTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="metaluser@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        self.profile = Profile.objects.get(user=self.user)
        self.portfolio = Portfolio.objects.create(profile=self.profile)

    def test_create_metal_portfolio_success(self):
        url = reverse('create-metal-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MetalPortfolio.objects.filter(portfolio=self.portfolio).exists())

    def test_create_metal_portfolio_twice_should_fail(self):
        MetalPortfolio.objects.create(portfolio=self.portfolio)
        url = reverse('create-metal-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)