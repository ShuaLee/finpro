from django.test import SimpleTestCase, override_settings

from apps.integrations.providers.fmp.parsers import parse_company_profile_payload, parse_quote_payload
from apps.integrations.providers.fmp.request import build_fmp_url


@override_settings(FMP_API_KEY="test-key")
class FMPRequestTests(SimpleTestCase):
    def test_build_fmp_url_uses_stable_base_and_api_key(self):
        url = build_fmp_url("/quote-short", symbol="AAPL")

        self.assertTrue(url.startswith("https://financialmodelingprep.com/stable/quote-short?"))
        self.assertIn("symbol=AAPL", url)
        self.assertIn("apikey=test-key", url)


class FMPParserTests(SimpleTestCase):
    def test_parse_quote_payload_normalizes_basic_fields(self):
        quote = parse_quote_payload(
            {
                "symbol": "aapl",
                "price": "210.15",
                "change": "1.25",
                "volume": "12345",
            },
            source="FMP",
        )

        self.assertEqual(quote.symbol, "AAPL")
        self.assertEqual(str(quote.price), "210.15")
        self.assertEqual(str(quote.change), "1.25")
        self.assertEqual(quote.volume, 12345)
        self.assertEqual(quote.source, "FMP")

    def test_parse_company_profile_payload_maps_core_fields(self):
        profile = parse_company_profile_payload(
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currency": "USD",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country": "US",
                "website": "https://apple.com",
                "description": "Maker of iPhones",
                "image": "https://example.com/aapl.png",
            }
        )

        self.assertEqual(profile.symbol, "AAPL")
        self.assertEqual(profile.name, "Apple Inc.")
        self.assertEqual(profile.exchange, "NASDAQ")
        self.assertEqual(profile.sector, "Technology")
