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
