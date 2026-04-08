from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import SupportedCountry, SupportedCurrency
from apps.users.services import ReferenceDataService


class ReferenceDataServiceTests(TestCase):
    @patch("apps.users.services.reference_data_service.MarketDataService.get_available_countries")
    def test_sync_supported_countries_creates_rows_from_provider(self, mock_get_countries):
        mock_get_countries.return_value = ["US", "CA"]

        result = ReferenceDataService.sync_supported_countries()

        self.assertEqual(result["total"], 2)
        self.assertTrue(SupportedCountry.objects.filter(code="US").exists())
        self.assertTrue(SupportedCountry.objects.filter(code="CA").exists())

    @patch("apps.users.services.reference_data_service.MarketDataService.get_forex_list")
    def test_sync_supported_currencies_creates_rows_from_provider(self, mock_get_forex_list):
        mock_get_forex_list.return_value = [
            {
                "fromCurrency": "USD",
                "fromName": "US Dollar",
                "toCurrency": "CAD",
                "toName": "Canadian Dollar",
            }
        ]

        result = ReferenceDataService.sync_supported_currencies()

        self.assertEqual(result["total"], 2)
        self.assertTrue(SupportedCurrency.objects.filter(code="USD", name="US Dollar").exists())
        self.assertTrue(SupportedCurrency.objects.filter(code="CAD", name="Canadian Dollar").exists())


class ReferenceDataApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
            email="refs@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)
        SupportedCountry.objects.create(code="CA", name="Canada")
        SupportedCurrency.objects.create(code="CAD", name="Canadian Dollar")

    def test_profile_options_returns_supported_countries_and_currencies(self):
        response = self.client.get(reverse("profile-options"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["countries"], [{"code": "CA", "name": "Canada"}])
        self.assertEqual(response.data["currencies"], [{"code": "CAD", "name": "Canadian Dollar"}])


class ReferenceDataManagementCommandTests(TestCase):
    @patch("apps.users.management.commands.sync_reference_data.ReferenceDataService.sync_supported_countries")
    @patch("apps.users.management.commands.sync_reference_data.ReferenceDataService.sync_supported_currencies")
    def test_sync_reference_data_command_calls_both_syncs(self, mock_sync_currencies, mock_sync_countries):
        mock_sync_countries.return_value = {"total": 2}
        mock_sync_currencies.return_value = {"total": 3}

        out = StringIO()
        call_command("sync_reference_data", stdout=out)

        mock_sync_countries.assert_called_once_with(deactivate_missing=False)
        mock_sync_currencies.assert_called_once_with(deactivate_missing=False)
        self.assertIn("countries", out.getvalue())
