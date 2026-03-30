from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import ReconciliationIssue


class ReconciliationService:
    @staticmethod
    @transaction.atomic
    def reconcile_positions(*, connection, external_positions: list[dict]):
        account = connection.account
        existing = {
            (h.original_ticker or "").upper(): h
            for h in account.holdings.select_related("asset").all()
            if h.original_ticker
        }
        seen_symbols = set()
        created = 0
        resolved = 0

        for row in external_positions:
            symbol = (row.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            seen_symbols.add(symbol)
            qty = Decimal(str(row.get("quantity", "0")))
            holding = existing.get(symbol)
            if not holding:
                ReconciliationIssue.objects.create(
                    account=account,
                    connection=connection,
                    issue_code=ReconciliationIssue.IssueCode.MISSING_INTERNAL_HOLDING,
                    severity=ReconciliationIssue.Severity.WARNING,
                    message=f"External position {symbol} not present internally.",
                    metadata={"symbol": symbol, "external_quantity": str(qty)},
                )
                created += 1
                continue
            if holding.quantity != qty:
                ReconciliationIssue.objects.create(
                    account=account,
                    connection=connection,
                    holding=holding,
                    issue_code=ReconciliationIssue.IssueCode.QUANTITY_MISMATCH,
                    severity=ReconciliationIssue.Severity.WARNING,
                    message=f"Quantity mismatch for {symbol}.",
                    metadata={"internal_quantity": str(holding.quantity), "external_quantity": str(qty)},
                )
                created += 1
            else:
                updated = ReconciliationIssue.objects.filter(
                    account=account,
                    connection=connection,
                    holding=holding,
                    issue_code=ReconciliationIssue.IssueCode.QUANTITY_MISMATCH,
                    status=ReconciliationIssue.Status.OPEN,
                ).update(status=ReconciliationIssue.Status.RESOLVED, resolved_at=timezone.now())
                resolved += updated

        for symbol, holding in existing.items():
            if symbol in seen_symbols:
                continue
            ReconciliationIssue.objects.create(
                account=account,
                connection=connection,
                holding=holding,
                issue_code=ReconciliationIssue.IssueCode.MISSING_EXTERNAL_HOLDING,
                severity=ReconciliationIssue.Severity.WARNING,
                message=f"Internal holding {symbol} missing externally.",
                metadata={"symbol": symbol, "internal_quantity": str(holding.quantity)},
            )
            created += 1

        return {"created": created, "resolved": resolved}

    @staticmethod
    @transaction.atomic
    def resolve_issue(
        *,
        issue: ReconciliationIssue,
        action: str,
        note: str | None = None,
    ):
        if issue.status != ReconciliationIssue.Status.OPEN:
            raise ValidationError("Issue is not open.")

        if action == ReconciliationIssue.ResolutionAction.ALIGN_TO_EXTERNAL:
            if issue.issue_code == ReconciliationIssue.IssueCode.MISSING_EXTERNAL_HOLDING:
                if issue.holding_id:
                    issue.holding.delete()
                    issue.holding = None
            elif issue.issue_code == ReconciliationIssue.IssueCode.QUANTITY_MISMATCH:
                external_quantity = issue.metadata.get("external_quantity")
                if issue.holding_id and external_quantity is not None:
                    issue.holding.quantity = Decimal(str(external_quantity))
                    issue.holding.save(update_fields=["quantity", "updated_at"])
            else:
                raise ValidationError("This issue type cannot be aligned directly.")
            new_status = ReconciliationIssue.Status.RESOLVED
        elif action == ReconciliationIssue.ResolutionAction.KEEP_INTERNAL:
            new_status = ReconciliationIssue.Status.IGNORED
        elif action == ReconciliationIssue.ResolutionAction.IGNORE:
            new_status = ReconciliationIssue.Status.IGNORED
        elif action == ReconciliationIssue.ResolutionAction.ADJUST_INTERNAL_QUANTITY:
            raise ValidationError("Use align_to_external for quantity adjustment.")
        else:
            raise ValidationError("Invalid reconciliation resolution action.")

        issue.resolution_action = action
        issue.resolution_note = (note or "").strip() or None
        issue.status = new_status
        issue.resolved_at = timezone.now()
        issue.save(
            update_fields=[
                "resolution_action",
                "resolution_note",
                "holding",
                "status",
                "resolved_at",
                "updated_at",
            ]
        )
        return issue
