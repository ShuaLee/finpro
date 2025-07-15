from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User, Profile
from portfolios.models.portfolio import Portfolio

class PortfolioEndpointTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        self.profile = Profile.objects.get(user=self.user)

    def test_create_portfolio_success(self):
        url = reverse('create-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Portfolio.objects.filter(profile=self.profile).exists())

    def test_create_portfolio_twice_should_fail(self):
        Portfolio.objects.create(profile=self.profile)
        url = reverse('create-portfolio')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Profile {} already has a portfolio.".format(self.profile.id))

    def test_get_portfolio_success(self):
        Portfolio.objects.create(profile=self.profile)
        url = reverse('portfolio-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data) 
        self.assertIn('created_at', response.data)

    def test_get_portfolio_when_none_exists(self):
        url = reverse('portfolio-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)