from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class RebuildEquityDirectoryCommandTests(TestCase):
    @patch("apps.integrations.management.commands.rebuild_equity_directory.EquityDirectorySyncService.rebuild_from_fmp")
    def test_rebuild_equity_directory_command_calls_service(self, mock_rebuild):
        mock_rebuild.return_value = {"snapshot_id": "1", "row_count": 2, "active_symbol_count": 1}

        out = StringIO()
        call_command("rebuild_equity_directory", stdout=out)

        mock_rebuild.assert_called_once_with()
        self.assertIn("row_count", out.getvalue())
