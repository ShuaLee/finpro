from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import BrokerageConnection, Holding
from assets.models.crypto import CryptoAsset
from assets.models.equity import EquityAsset

from .brokerage_adapters import BrokeragePosition, get_adapter
from .audit_service import AccountAuditService
from .reconciliation_service import ReconciliationService
from .snapshot_service import HoldingSnapshotService


class BrokerageSyncService:
    @staticmethod
    def _assert_sync_supported(account):
        allowed = set(account.allowed_asset_types.values_list("slug", flat=True))
        supported = {"equity", "crypto"}
        if not allowed:
            raise ValidationError("Account has no asset type restrictions configured for sync.")
        if not allowed.issubset(supported):
            raise ValidationError(
                "Brokerage sync supports account types restricted to equity and/or crypto."
            )

    @staticmethod
    def _resolve_asset(*, symbol: str, allowed_asset_type_slugs: set[str]):
        if "equity" in allowed_asset_type_slugs:
            equity = EquityAsset.objects.filter(ticker__iexact=symbol).select_related("asset").first()
            if equity:
                return equity.asset

        if "crypto" in allowed_asset_type_slugs:
            crypto = (
                CryptoAsset.objects.filter(base_symbol__iexact=symbol)
                .select_related("asset")
                .first()
            )
            if crypto:
                return crypto.asset

            crypto_pair = (
                CryptoAsset.objects.filter(pair_symbol__iexact=symbol)
                .select_related("asset")
                .first()
            )
            if crypto_pair:
                return crypto_pair.asset

        return None

    @staticmethod
    @transaction.atomic
    def sync_connection(*, connection: BrokerageConnection, prune_missing: bool = False):
        account = connection.account
        BrokerageSyncService._assert_sync_supported(account)

        if connection.provider != BrokerageConnection.Provider.MANUAL and not connection.access_token_ref:
            raise ValidationError("Connection has no token reference. Reconnect the provider.")

        adapter = get_adapter(connection.provider)
        positions = adapter.fetch_positions(connection)
        return BrokerageSyncService._apply_positions(
            connection=connection,
            positions=positions,
            prune_missing=prune_missing,
        )

    @staticmethod
    @transaction.atomic
    def sync_from_payload(*, connection: BrokerageConnection, positions: list[dict], prune_missing: bool = False):
        account = connection.account
        BrokerageSyncService._assert_sync_supported(account)

        normalized: list[BrokeragePosition] = []
        for row in positions:
            symbol = (row.get("symbol") or "").strip().upper()
            quantity = row.get("quantity")
            if not symbol or quantity is None:
                continue
            average_cost = row.get("average_cost")
            normalized.append(
                BrokeragePosition(
                    symbol=symbol,
                    quantity=Decimal(str(quantity)),
                    average_cost=Decimal(str(average_cost)) if average_cost is not None else None,
                )
            )

        return BrokerageSyncService._apply_positions(
            connection=connection,
            positions=normalized,
            prune_missing=prune_missing,
        )

    @staticmethod
    def _apply_positions(*, connection: BrokerageConnection, positions: list[BrokeragePosition], prune_missing: bool):
        account = connection.account
        allowed_asset_type_slugs = set(
            account.allowed_asset_types.values_list("slug", flat=True)
        )

        updated = 0
        created = 0
        skipped = 0
        seen_asset_ids = set()

        for pos in positions:
            asset = BrokerageSyncService._resolve_asset(
                symbol=pos.symbol,
                allowed_asset_type_slugs=allowed_asset_type_slugs,
            )
            if not asset:
                skipped += 1
                continue

            seen_asset_ids.add(str(asset.id))

            holding, was_created = Holding.objects.get_or_create(
                account=account,
                asset=asset,
                defaults={
                    "quantity": pos.quantity,
                    "average_purchase_price": pos.average_cost,
                    "original_ticker": pos.symbol,
                    "tracking_mode": Holding.TrackingMode.TRACKED,
                    "price_source_mode": Holding.PriceSourceMode.MARKET,
                },
            )
            if was_created:
                created += 1
                continue

            changed = False
            if holding.quantity != pos.quantity:
                holding.quantity = pos.quantity
                changed = True
            if holding.average_purchase_price != pos.average_cost:
                holding.average_purchase_price = pos.average_cost
                changed = True
            if not holding.original_ticker:
                holding.original_ticker = pos.symbol
                changed = True
            if changed:
                holding.save(update_fields=["quantity", "average_purchase_price", "original_ticker", "updated_at"])
                updated += 1

        removed = 0
        if prune_missing:
            qs = Holding.objects.filter(account=account, asset__isnull=False)
            for holding in qs.select_related("asset"):
                if str(holding.asset_id) not in seen_asset_ids:
                    holding.delete()
                    removed += 1

        account.last_synced = timezone.now()
        account.save(update_fields=["last_synced"])

        connection.status = BrokerageConnection.Status.ACTIVE
        connection.last_error = None
        connection.last_synced_at = timezone.now()
        connection.save(update_fields=["status", "last_error", "last_synced_at", "updated_at"])

        ReconciliationService.reconcile_positions(
            connection=connection,
            external_positions=[
                {"symbol": p.symbol, "quantity": str(p.quantity)}
                for p in positions
            ],
        )
        HoldingSnapshotService.capture_account(account=account, source="sync")
        AccountAuditService.log(
            account=account,
            action="connection.synced",
            metadata={
                "connection_id": connection.id,
                "provider": connection.provider,
                "created": created,
                "updated": updated,
                "removed": removed,
                "skipped": skipped,
            },
        )

        return {
            "created": created,
            "updated": updated,
            "removed": removed,
            "skipped": skipped,
        }
