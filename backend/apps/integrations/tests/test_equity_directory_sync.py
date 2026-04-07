from unittest.mock import patch

from django.test import TestCase

from apps.integrations.models import EquityDirectoryEntry, EquityDirectorySnapshot
from apps.integrations.services import EquityDirectorySyncService


class EquityDirectorySyncServiceTests(TestCase):
    @patch("apps.integrations.services.equity_directory_sync_service.FMP_PROVIDER.get_actively_traded_symbols")
    @patch("apps.integrations.services.equity_directory_sync_service.FMP_PROVIDER.get_stock_list")
    def test_rebuild_creates_new_active_snapshot(self, mock_get_stock_list, mock_get_active_symbols):
        mock_get_stock_list.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "exchange": "NASDAQ", "currency": "USD"},
        ]
        mock_get_active_symbols.return_value = {"AAPL"}

        result = EquityDirectorySyncService.rebuild_from_fmp()

        self.assertEqual(result["row_count"], 2)
        snapshot = EquityDirectorySnapshot.objects.get(is_active=True)
        self.assertEqual(snapshot.row_count, 2)
        self.assertEqual(snapshot.entries.count(), 2)
        self.assertTrue(
            EquityDirectoryEntry.objects.filter(
                snapshot=snapshot,
                symbol="AAPL",
                is_actively_traded=True,
            ).exists()
        )

    @patch("apps.integrations.services.equity_directory_sync_service.FMP_PROVIDER.get_actively_traded_symbols")
    @patch("apps.integrations.services.equity_directory_sync_service.FMP_PROVIDER.get_stock_list")
    def test_rebuild_deactivates_previous_snapshot(self, mock_get_stock_list, mock_get_active_symbols):
        mock_get_stock_list.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"},
        ]
        mock_get_active_symbols.return_value = {"AAPL"}
        EquityDirectorySyncService.rebuild_from_fmp()

        first_snapshot = EquityDirectorySnapshot.objects.get(is_active=True)

        mock_get_stock_list.return_value = [
            {"symbol": "MSFT", "name": "Microsoft Corp.", "exchange": "NASDAQ", "currency": "USD"},
        ]
        mock_get_active_symbols.return_value = {"MSFT"}
        EquityDirectorySyncService.rebuild_from_fmp()

        first_snapshot.refresh_from_db()
        self.assertFalse(first_snapshot.is_active)
        self.assertEqual(EquityDirectorySnapshot.objects.filter(is_active=True).count(), 1)
