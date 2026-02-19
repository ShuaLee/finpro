from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from external_data.exceptions import (
    ExternalDataAccessDenied,
    ExternalDataProviderUnavailable,
    ExternalDataRateLimited,
    ExternalDataUnauthorized,
)
from external_data.providers.fmp.equities.fetchers import fetch_equity_quote_short
from external_data.providers.fmp.request import build_fmp_url
from external_data.shared.http import get_json
from external_data.shared.provider_guard import ProviderGuard


class ExternalDataHTTPTests(SimpleTestCase):
    @patch("external_data.shared.http.requests.get")
    def test_http_maps_403_to_access_denied(self, mock_get):
        response = Mock()
        response.status_code = 403
        mock_get.return_value = response

        with self.assertRaises(ExternalDataAccessDenied):
            get_json("https://example.com")

    @patch("external_data.shared.http.requests.get")
    def test_http_maps_401_to_unauthorized(self, mock_get):
        response = Mock()
        response.status_code = 401
        mock_get.return_value = response

        with self.assertRaises(ExternalDataUnauthorized):
            get_json("https://example.com")

    @patch("external_data.shared.http.requests.get")
    def test_http_retries_then_rate_limited(self, mock_get):
        response = Mock()
        response.status_code = 429
        response.headers = {}
        mock_get.return_value = response

        with self.assertRaises(ExternalDataRateLimited):
            get_json("https://example.com", max_retries=1, backoff_seconds=0)

        self.assertEqual(mock_get.call_count, 2)


class ProviderGuardTests(SimpleTestCase):
    def test_guard_does_not_count_access_denied_as_outage(self):
        provider = Mock()
        provider.test_call.side_effect = ExternalDataAccessDenied("no plan access")
        guard = ProviderGuard(name="FMP", provider=provider)

        with self.assertRaises(ExternalDataAccessDenied):
            guard.test_call()

        self.assertEqual(guard.consecutive_failures, 0)

    def test_guard_opens_after_max_failures(self):
        provider = Mock()
        provider.test_call.side_effect = ExternalDataProviderUnavailable("outage")
        guard = ProviderGuard(name="FMP", provider=provider)

        for _ in range(guard.MAX_FAILURES):
            with self.assertRaises(ExternalDataProviderUnavailable):
                guard.test_call()

        with self.assertRaises(ExternalDataProviderUnavailable):
            guard.test_call()


class FMPRequestHelpersTests(SimpleTestCase):
    @patch("external_data.providers.fmp.request.FMP_API_KEY", "test-key")
    def test_build_fmp_url_includes_api_key_and_params(self):
        url = build_fmp_url("/quote-short", symbol="AAPL")
        self.assertIn("apikey=", url)
        self.assertIn("symbol=AAPL", url)

    @patch("external_data.providers.fmp.request.FMP_API_KEY", "")
    def test_build_fmp_url_requires_api_key(self):
        with self.assertRaises(ExternalDataProviderUnavailable):
            build_fmp_url("/quote-short", symbol="AAPL")

    @patch("external_data.providers.fmp.equities.fetchers.fmp_get_json")
    def test_equity_quote_fetcher_validates_response_shape(self, mock_get_json):
        mock_get_json.return_value = [{"price": "12.3", "change": "0.2", "volume": 10}]
        parsed = fetch_equity_quote_short("AAPL")
        self.assertEqual(str(parsed["price"]), "12.3")
