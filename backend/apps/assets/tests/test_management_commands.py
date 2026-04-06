from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.assets.management.commands.seed_asset_types import SYSTEM_ASSET_TYPES
from apps.assets.models import AssetType


class SeedAssetTypesCommandTests(TestCase):
    def test_seed_asset_types_creates_and_is_idempotent(self):
        out = StringIO()

        call_command("seed_asset_types", stdout=out)

        seeded_names = set(
            AssetType.objects.filter(created_by__isnull=True).values_list("name", flat=True)
        )
        expected_names = {item["name"] for item in SYSTEM_ASSET_TYPES}

        self.assertTrue(expected_names.issubset(seeded_names))

        first_count = AssetType.objects.filter(created_by__isnull=True).count()

        out = StringIO()
        call_command("seed_asset_types", stdout=out)
        second_count = AssetType.objects.filter(created_by__isnull=True).count()

        self.assertEqual(first_count, second_count)

    @patch("apps.assets.management.commands.sync_public_assets.PublicAssetSyncService.sync_symbols")
    def test_sync_public_assets_command_calls_service(self, mock_sync_symbols):
        mock_sync_symbols.return_value = {"created_or_updated": 1, "unresolved": 0, "errors": 0}

        out = StringIO()
        call_command("sync_public_assets", "AAPL", "MSFT", stdout=out)

        mock_sync_symbols.assert_called_once()
        self.assertIn("created_or_updated", out.getvalue())

    @patch("apps.assets.management.commands.sync_public_equity_directory.PublicAssetSyncService.sync_equity_directory")
    def test_sync_public_equity_directory_command_calls_service(self, mock_sync_equity_directory):
        mock_sync_equity_directory.return_value = {"created": 10, "updated": 20, "deactivated": 3}

        out = StringIO()
        call_command("sync_public_equity_directory", stdout=out)

        mock_sync_equity_directory.assert_called_once_with()
        self.assertIn("created", out.getvalue())
