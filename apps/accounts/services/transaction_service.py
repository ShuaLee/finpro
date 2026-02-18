from decimal import Decimal
from datetime import datetime, time

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import AccountTransaction, Holding
from assets.models.crypto import CryptoAsset
from assets.models.equity import EquityAsset

from .audit_service import AccountAuditService
from .holding_service import HoldingService


class TransactionService:
    @staticmethod
    def _normalize_datetime(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value)
            return value
        if isinstance(value, str):
            dt = parse_datetime(value)
            if dt is not None:
                return dt
            d = parse_date(value)
            if d is not None:
                return timezone.make_aware(datetime.combine(d, time.min))
        raise ValidationError("Invalid transaction datetime.")

    @staticmethod
    def _resolve_asset(*, symbol: str):
        symbol = (symbol or "").strip().upper()
        if not symbol:
            return None
        equity = EquityAsset.objects.filter(ticker__iexact=symbol).select_related("asset").first()
        if equity:
            return equity.asset
        crypto = CryptoAsset.objects.filter(base_symbol__iexact=symbol).select_related("asset").first()
        if crypto:
            return crypto.asset
        crypto_pair = CryptoAsset.objects.filter(pair_symbol__iexact=symbol).select_related("asset").first()
        if crypto_pair:
            return crypto_pair.asset
        return None

    @staticmethod
    def _apply_to_holdings_if_needed(*, account, transaction_obj: AccountTransaction):
        if account.position_mode not in {account.PositionMode.LEDGER, account.PositionMode.HYBRID}:
            return

        if not transaction_obj.asset_id or transaction_obj.quantity is None:
            return

        holding = Holding.objects.filter(account=account, asset_id=transaction_obj.asset_id).first()
        qty_delta = transaction_obj.quantity
        if transaction_obj.event_type in {AccountTransaction.EventType.SELL, AccountTransaction.EventType.TRANSFER_OUT}:
            qty_delta = -qty_delta
        elif transaction_obj.event_type not in {
            AccountTransaction.EventType.BUY,
            AccountTransaction.EventType.TRANSFER_IN,
            AccountTransaction.EventType.ADJUSTMENT,
        }:
            return

        if not holding:
            if qty_delta < 0:
                raise ValidationError("Cannot apply negative ledger quantity to a missing holding.")
            HoldingService.create(
                account=account,
                asset=transaction_obj.asset,
                quantity=qty_delta,
                average_purchase_price=transaction_obj.unit_price,
            )
            return

        new_qty = holding.quantity + qty_delta
        if new_qty < 0:
            raise ValidationError("Transaction would make holding quantity negative.")
        holding.quantity = new_qty
        if transaction_obj.unit_price is not None and new_qty > 0 and transaction_obj.event_type == AccountTransaction.EventType.BUY:
            holding.average_purchase_price = transaction_obj.unit_price
        holding.save()

    @staticmethod
    @transaction.atomic
    def create_manual(
        *,
        account,
        actor,
        event_type: str,
        traded_at,
        quantity=None,
        unit_price=None,
        gross_amount=None,
        fees=None,
        taxes=None,
        net_amount=None,
        currency=None,
        note=None,
        asset=None,
        symbol: str | None = None,
    ):
        if asset is None and symbol:
            asset = TransactionService._resolve_asset(symbol=symbol)

        tx = AccountTransaction.objects.create(
            account=account,
            asset=asset,
            event_type=event_type,
            source=AccountTransaction.Source.MANUAL,
            traded_at=traded_at,
            quantity=quantity,
            unit_price=unit_price,
            gross_amount=gross_amount,
            fees=fees,
            taxes=taxes,
            net_amount=net_amount,
            currency=currency,
            note=note,
        )
        TransactionService._apply_to_holdings_if_needed(account=account, transaction_obj=tx)
        AccountAuditService.log(
            account=account,
            actor=actor,
            action="transaction.manual.created",
            metadata={"transaction_id": tx.id},
        )
        return tx

    @staticmethod
    @transaction.atomic
    def ingest_external(
        *,
        account,
        source: str,
        payload_rows: list[dict],
    ):
        created = 0
        updated = 0

        for row in payload_rows:
            external_id = row.get("external_transaction_id")
            if not external_id:
                continue
            symbol = row.get("symbol")
            asset = TransactionService._resolve_asset(symbol=symbol)
            defaults = {
                "asset": asset,
                "event_type": row["event_type"],
                "traded_at": TransactionService._normalize_datetime(row["traded_at"]),
                "settled_at": TransactionService._normalize_datetime(row.get("settled_at")),
                "quantity": Decimal(str(row["quantity"])) if row.get("quantity") is not None else None,
                "unit_price": Decimal(str(row["unit_price"])) if row.get("unit_price") is not None else None,
                "gross_amount": Decimal(str(row["gross_amount"])) if row.get("gross_amount") is not None else None,
                "fees": Decimal(str(row["fees"])) if row.get("fees") is not None else None,
                "taxes": Decimal(str(row["taxes"])) if row.get("taxes") is not None else None,
                "net_amount": Decimal(str(row["net_amount"])) if row.get("net_amount") is not None else None,
                "currency": row.get("currency"),
                "note": row.get("note"),
                "raw_payload": row.get("raw_payload", {}),
            }
            tx, was_created = AccountTransaction.objects.update_or_create(
                account=account,
                source=source,
                external_transaction_id=external_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1
            TransactionService._apply_to_holdings_if_needed(account=account, transaction_obj=tx)

        return {"created": created, "updated": updated}
