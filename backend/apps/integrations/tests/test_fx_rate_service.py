from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.integrations.models import FXRateCache
from apps.integrations.services import FXRateService
from apps.integrations.shared.types import QuoteSnapshot


@override_settings(FX_RATE_CACHE_TTL_SECONDS=3600)
class FXRateServiceTests(TestCase):
    @patch("apps.integrations.services.fx_rate_service.FMP_PROVIDER.get_quote")
    def test_get_rate_fetches_and_caches_pair(self, mock_get_quote):
        mock_get_quote.return_value = QuoteSnapshot(
            symbol="CADUSD",
            price=Decimal("0.7401"),
            source="FMP",
        )

        rate = FXRateService.get_rate(base_currency="CAD", quote_currency="USD")

        self.assertEqual(rate, Decimal("0.7401"))
        self.assertTrue(
            FXRateCache.objects.filter(
                provider="fmp",
                base_currency="CAD",
                quote_currency="USD",
                pair_symbol="CADUSD",
            ).exists()
        )
        mock_get_quote.assert_called_once_with("CADUSD")

    @patch("apps.integrations.services.fx_rate_service.FMP_PROVIDER.get_quote")
    def test_get_rate_uses_cache_when_fresh(self, mock_get_quote):
        FXRateCache.objects.create(
            provider="fmp",
            base_currency="EUR",
            quote_currency="USD",
            pair_symbol="EURUSD",
            rate=Decimal("1.08"),
        )

        rate = FXRateService.get_rate(base_currency="EUR", quote_currency="USD")

        self.assertEqual(rate, Decimal("1.08"))
        mock_get_quote.assert_not_called()
