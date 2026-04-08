from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.assets.models import AssetType


class AssetManagementCommandTests(TestCase):
    def test_seed_asset_types_command_is_idempotent(self):
        out = StringIO()

        call_command("seed_asset_types", stdout=out)
        first_count = AssetType.objects.filter(created_by__isnull=True).count()

        call_command("seed_asset_types", stdout=out)
        second_count = AssetType.objects.filter(created_by__isnull=True).count()

        self.assertEqual(first_count, second_count)
        self.assertGreater(first_count, 0)

    @patch("apps.assets.management.commands.sync_public_asset_dividends.AssetDividendService.sync_assets")
    def test_sync_public_asset_dividends_command_calls_service(self, mock_sync_assets):
        mock_sync_assets.return_value = {"synced": 1, "inactive": 0, "errors": 0}

        out = StringIO()
        call_command("sync_public_asset_dividends", stdout=out)

        mock_sync_assets.assert_called_once()
        self.assertIn("synced", out.getvalue())
