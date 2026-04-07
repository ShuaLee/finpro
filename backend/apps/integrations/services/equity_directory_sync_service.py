from django.db import transaction

from apps.integrations.models import EquityDirectoryEntry, EquityDirectorySnapshot
from apps.integrations.providers.fmp import FMP_PROVIDER


class EquityDirectorySyncService:
    @staticmethod
    def get_active_snapshot(*, provider: str = "fmp"):
        return EquityDirectorySnapshot.objects.filter(
            provider=provider,
            is_active=True,
        ).first()

    @staticmethod
    def get_active_entries(*, provider: str = "fmp"):
        snapshot = EquityDirectorySyncService.get_active_snapshot(provider=provider)
        if snapshot is None:
            return EquityDirectoryEntry.objects.none()
        return snapshot.entries.all()

    @staticmethod
    @transaction.atomic
    def rebuild_from_fmp() -> dict:
        stock_rows = FMP_PROVIDER.get_stock_list()
        active_symbols = FMP_PROVIDER.get_actively_traded_symbols()

        EquityDirectorySnapshot.objects.filter(provider="fmp", is_active=True).update(is_active=False)
        snapshot = EquityDirectorySnapshot.objects.create(provider="fmp", is_active=True)

        entries = [
            EquityDirectoryEntry(
                snapshot=snapshot,
                symbol=row["symbol"],
                name=row["name"],
                exchange=row.get("exchange", ""),
                currency=row.get("currency", ""),
                is_actively_traded=row["symbol"] in active_symbols,
                source_payload=row,
            )
            for row in stock_rows
        ]
        EquityDirectoryEntry.objects.bulk_create(entries, batch_size=5000)

        snapshot.row_count = len(entries)
        snapshot.save(update_fields=["row_count"])

        return {
            "snapshot_id": str(snapshot.id),
            "row_count": snapshot.row_count,
            "active_symbol_count": len(active_symbols),
        }
