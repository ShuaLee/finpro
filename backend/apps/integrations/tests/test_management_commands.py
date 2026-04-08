from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class RebuildEquityDirectoryCommandTests(TestCase):
    @patch("apps.integrations.management.commands.refresh_active_equities.HeldEquityReviewService.review_all_tracked_equities")
    @patch("apps.integrations.management.commands.refresh_active_equities.ActiveEquitySyncService.refresh_from_fmp")
    def test_refresh_active_equities_command_calls_services(self, mock_refresh, mock_review):
        mock_refresh.return_value = {"provider": "fmp", "row_count": 2}
        mock_review.return_value = {"tracked": 1, "needs_review": 0, "stale": 0, "skipped": 0}

        out = StringIO()
        call_command("refresh_active_equities", stdout=out)

        mock_refresh.assert_called_once_with()
        mock_review.assert_called_once_with()
        self.assertIn("active_list", out.getvalue())

    @patch("apps.integrations.management.commands.refresh_active_market_lists.HeldMarketAssetReviewService.review_all_tracked_assets")
    @patch("apps.integrations.management.commands.refresh_active_market_lists.HeldEquityReviewService.review_all_tracked_equities")
    @patch("apps.integrations.management.commands.refresh_active_market_lists.ActiveCommoditySyncService.refresh_from_fmp")
    @patch("apps.integrations.management.commands.refresh_active_market_lists.ActiveCryptoSyncService.refresh_from_fmp")
    @patch("apps.integrations.management.commands.refresh_active_market_lists.ActiveEquitySyncService.refresh_from_fmp")
    def test_refresh_active_market_lists_command_calls_all_services(
        self,
        mock_equity_refresh,
        mock_crypto_refresh,
        mock_commodity_refresh,
        mock_equity_review,
        mock_market_review,
    ):
        mock_equity_refresh.return_value = {"provider": "fmp", "row_count": 2}
        mock_crypto_refresh.return_value = {"provider": "fmp", "row_count": 3}
        mock_commodity_refresh.return_value = {"provider": "fmp", "row_count": 4}
        mock_equity_review.return_value = {"tracked": 1, "needs_review": 0, "stale": 0, "skipped": 0}
        mock_market_review.return_value = {"tracked": 1, "stale": 0, "skipped": 0}

        out = StringIO()
        call_command("refresh_active_market_lists", stdout=out)

        mock_equity_refresh.assert_called_once_with()
        mock_crypto_refresh.assert_called_once_with()
        mock_commodity_refresh.assert_called_once_with()
        mock_equity_review.assert_called_once_with()
        mock_market_review.assert_called_once_with()
        self.assertIn("cryptos", out.getvalue())
