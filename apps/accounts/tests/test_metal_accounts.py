from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User
from portfolios.models import Portfolio, MetalPortfolio
from accounts.models import StorageFacility

class MetalAccountTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testmetal@example.com", password="pass")
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(profile=self.user.profile)
        self.metal_portfolio = MetalPortfolio.objects.create(portfolio=self.portfolio)

    def test_create_storage_facility(self):
        url = reverse('storage-facility')
        data = {"name": "Vault A", "is_lending_account": True, "is_insured": True, "interest_rate": "2.5"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StorageFacility.objects.count(), 1)

    def test_list_storage_facilities(self):
        StorageFacility.objects.create(metals_portfolio=self.metal_portfolio, name="Vault A")
        url = reverse('storage-facility')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
