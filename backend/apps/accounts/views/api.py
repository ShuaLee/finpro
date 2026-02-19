from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    Account,
    AccountTransaction,
    AccountType,
    BrokerageConnection,
    Holding,
    ReconciliationIssue,
    AccountJob,
)
from accounts.serializers import (
    AccountCreateSerializer,
    AccountSerializer,
    AccountTypeSerializer,
    BrokerageConnectionCreateSerializer,
    BrokerageConnectionSerializer,
    BrokerageLinkSessionCreateSerializer,
    BrokerageSyncPayloadSerializer,
    CustomAccountTypeCreateSerializer,
    HoldingCreateSerializer,
    HoldingSerializer,
    ReconciliationIssueSerializer,
    ReconciliationIssueUpdateSerializer,
    SnapshotSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
    JobSerializer,
)
from accounts.services import (
    AccountDashboardService,
    AccountDeletionService,
    AccountService,
    BrokerageConnectionService,
    BrokerageSyncService,
    HoldingSnapshotService,
    HoldingService,
    ReconciliationService,
    TransactionService,
    AccountJobService,
)
from accounts.services.brokerage_adapters import get_adapter
from assets.models.core import Asset, AssetType
from fx.models.fx import FXCurrency


def _owned_account_or_404(*, account_id: int, user):
    return get_object_or_404(
        Account.objects.select_related("portfolio__profile", "account_type"),
        id=account_id,
        portfolio__profile__user=user,
    )


def _owned_holding_or_404(*, holding_id: int, user):
    return get_object_or_404(
        Holding.objects.select_related("account__portfolio__profile"),
        id=holding_id,
        account__portfolio__profile__user=user,
    )


class AccountTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        queryset = AccountType.objects.filter(is_system=True) | AccountType.objects.filter(owner=profile)
        queryset = queryset.prefetch_related("allowed_asset_types").order_by("name")
        return Response(AccountTypeSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class CustomAccountTypeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CustomAccountTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            account_type = AccountService.create_custom_account_type(
                profile=request.user.profile,
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description"),
                allowed_asset_type_slugs=serializer.validated_data["allowed_asset_type_slugs"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AccountTypeSerializer(account_type).data, status=status.HTTP_201_CREATED)


class AccountListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Account.objects.filter(portfolio__profile__user=request.user)
            .select_related("portfolio", "account_type", "classification")
            .order_by("name")
        )
        return Response(AccountSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            account = AccountService.create_account(
                profile=request.user.profile,
                portfolio_id=serializer.validated_data["portfolio_id"],
                name=serializer.validated_data["name"],
                account_type_id=serializer.validated_data["account_type_id"],
                broker=serializer.validated_data.get("broker"),
                classification_definition_id=serializer.validated_data["classification_definition_id"],
                position_mode=serializer.validated_data.get("position_mode"),
                allow_manual_overrides=serializer.validated_data.get("allow_manual_overrides"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AccountSerializer(account).data, status=status.HTTP_201_CREATED)


class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        return Response(AccountSerializer(account).data, status=status.HTTP_200_OK)

    def patch(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        allowed_fields = {"name", "broker", "position_mode", "allow_manual_overrides"}
        payload = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = AccountSerializer(account, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        AccountDeletionService.delete_account(account=account)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HoldingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        holdings = account.holdings.select_related("asset", "asset__asset_type").all()
        return Response(HoldingSerializer(holdings, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        serializer = HoldingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset = None
        if serializer.validated_data.get("asset_id"):
            asset = get_object_or_404(Asset, id=serializer.validated_data["asset_id"])

        asset_type = None
        if serializer.validated_data.get("asset_type_slug"):
            asset_type = get_object_or_404(AssetType, slug=serializer.validated_data["asset_type_slug"])

        currency = None
        if serializer.validated_data.get("currency_code"):
            currency = get_object_or_404(FXCurrency, code=serializer.validated_data["currency_code"].upper())

        try:
            holding = HoldingService.create(
                account=account,
                quantity=serializer.validated_data["quantity"],
                average_purchase_price=serializer.validated_data.get("average_purchase_price"),
                asset=asset,
                asset_type=asset_type,
                custom_name=serializer.validated_data.get("custom_name"),
                currency=currency,
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(HoldingSerializer(holding).data, status=status.HTTP_201_CREATED)


class HoldingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, holding_id: int):
        holding = _owned_holding_or_404(holding_id=holding_id, user=request.user)
        quantity = request.data.get("quantity", holding.quantity)
        average_purchase_price = request.data.get(
            "average_purchase_price",
            holding.average_purchase_price,
        )
        try:
            holding = HoldingService.update(
                holding=holding,
                quantity=quantity,
                average_purchase_price=average_purchase_price,
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(HoldingSerializer(holding).data, status=status.HTTP_200_OK)

    def delete(self, request, holding_id: int):
        holding = _owned_holding_or_404(holding_id=holding_id, user=request.user)
        holding.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountsSidebarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = AccountDashboardService.sidebar_groups_for_profile(profile=request.user.profile)
        return Response(payload, status=status.HTTP_200_OK)


class BrokerageConnectionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = BrokerageConnection.objects.filter(
            account__portfolio__profile__user=request.user
        ).select_related("account")
        return Response(BrokerageConnectionSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BrokerageConnectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = _owned_account_or_404(
            account_id=serializer.validated_data["account_id"],
            user=request.user,
        )
        try:
            connection = BrokerageConnectionService.connect_read_only(
                account=account,
                provider=serializer.validated_data["provider"],
                source_type=serializer.validated_data.get("source_type"),
                public_token=serializer.validated_data.get("public_token"),
                token_ref=serializer.validated_data.get("token_ref"),
                external_account_id=serializer.validated_data.get("external_account_id"),
                connection_label=serializer.validated_data.get("connection_label"),
                consent_expires_at=serializer.validated_data.get("consent_expires_at"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BrokerageConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)


class BrokerageConnectionLinkSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BrokerageLinkSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = _owned_account_or_404(
            account_id=serializer.validated_data["account_id"],
            user=request.user,
        )

        try:
            payload = BrokerageConnectionService.create_link_session(
                provider=serializer.validated_data["provider"],
                redirect_uri=serializer.validated_data.get("redirect_uri"),
                user_id=str(request.user.id),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "account_id": account.id,
                "provider": serializer.validated_data["provider"],
                "source_type": serializer.validated_data.get("source_type"),
                "session": payload,
            },
            status=status.HTTP_200_OK,
        )


class BrokerageConnectionSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(
            BrokerageConnection.objects.select_related("account__portfolio__profile"),
            id=connection_id,
            account__portfolio__profile__user=request.user,
        )
        try:
            prune_missing = bool(request.data.get("prune_missing", False))
            async_mode = bool(request.data.get("async", False))
            if async_mode:
                job = AccountJobService.enqueue(
                    account=connection.account,
                    connection=connection,
                    job_type=AccountJob.JobType.SYNC_POSITIONS,
                    payload={"prune_missing": prune_missing},
                    idempotency_key=f"sync_positions:{connection.id}:{prune_missing}",
                )
                return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
            summary = BrokerageSyncService.sync_connection(connection=connection, prune_missing=prune_missing)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            connection.status = BrokerageConnection.Status.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["status", "last_error", "updated_at"])
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(summary, status=status.HTTP_200_OK)


class BrokerageConnectionSyncTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(
            BrokerageConnection.objects.select_related("account__portfolio__profile"),
            id=connection_id,
            account__portfolio__profile__user=request.user,
        )
        try:
            async_mode = bool(request.data.get("async", False))
            days = int(request.data.get("days", 30))
            if async_mode:
                job = AccountJobService.enqueue(
                    account=connection.account,
                    connection=connection,
                    job_type=AccountJob.JobType.SYNC_TRANSACTIONS,
                    payload={"days": days},
                    idempotency_key=f"sync_transactions:{connection.id}:{days}",
                )
                return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
            adapter = get_adapter(connection.provider)
            rows = adapter.fetch_transactions(connection, days=days)
            result = TransactionService.ingest_external(
                account=connection.account,
                source=AccountTransaction.Source.PLAID if connection.provider == BrokerageConnection.Provider.PLAID else AccountTransaction.Source.IMPORT,
                payload_rows=rows,
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            connection.status = BrokerageConnection.Status.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["status", "last_error", "updated_at"])
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result, status=status.HTTP_200_OK)


class BrokerageConnectionSyncPayloadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(
            BrokerageConnection.objects.select_related("account__portfolio__profile"),
            id=connection_id,
            account__portfolio__profile__user=request.user,
        )
        serializer = BrokerageSyncPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            summary = BrokerageSyncService.sync_from_payload(
                connection=connection,
                positions=serializer.validated_data["positions"],
                prune_missing=serializer.validated_data["prune_missing"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(summary, status=status.HTTP_200_OK)


class TransactionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        queryset = account.transactions.select_related("currency", "holding", "asset").all()
        return Response(TransactionSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        serializer = TransactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        currency = None
        if serializer.validated_data.get("currency_code"):
            currency = get_object_or_404(FXCurrency, code=serializer.validated_data["currency_code"].upper())

        asset = None
        if serializer.validated_data.get("asset_id"):
            asset = get_object_or_404(Asset, id=serializer.validated_data["asset_id"])

        try:
            tx = TransactionService.create_manual(
                account=account,
                actor=request.user,
                event_type=serializer.validated_data["event_type"],
                traded_at=serializer.validated_data["traded_at"],
                quantity=serializer.validated_data.get("quantity"),
                unit_price=serializer.validated_data.get("unit_price"),
                gross_amount=serializer.validated_data.get("gross_amount"),
                fees=serializer.validated_data.get("fees"),
                taxes=serializer.validated_data.get("taxes"),
                net_amount=serializer.validated_data.get("net_amount"),
                currency=currency,
                note=serializer.validated_data.get("note"),
                asset=asset,
                symbol=serializer.validated_data.get("symbol"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, transaction_id: int):
        tx = get_object_or_404(
            AccountTransaction.objects.select_related("account__portfolio__profile"),
            id=transaction_id,
            account__portfolio__profile__user=request.user,
        )
        tx.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountSnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        async_mode = bool(request.data.get("async", False))
        if async_mode:
            job = AccountJobService.enqueue(
                account=account,
                job_type=AccountJob.JobType.SNAPSHOT,
                payload={},
                idempotency_key=f"snapshot:{account.id}",
            )
            return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
        snapshots = HoldingSnapshotService.capture_account(account=account, source="manual")
        return Response(SnapshotSerializer(snapshots, many=True).data, status=status.HTTP_201_CREATED)


class ReconciliationIssueListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id: int):
        account = _owned_account_or_404(account_id=account_id, user=request.user)
        qs = ReconciliationIssue.objects.filter(account=account).order_by("-created_at")
        return Response(ReconciliationIssueSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class ReconciliationIssueDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, issue_id: int):
        issue = get_object_or_404(
            ReconciliationIssue.objects.select_related("account__portfolio__profile"),
            id=issue_id,
            account__portfolio__profile__user=request.user,
        )
        serializer = ReconciliationIssueUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data.get("resolution_action")
        note = serializer.validated_data.get("resolution_note")

        if action:
            try:
                issue = ReconciliationService.resolve_issue(
                    issue=issue,
                    action=action,
                    note=note,
                )
            except DjangoValidationError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            issue.status = serializer.validated_data["status"]
            if issue.status == ReconciliationIssue.Status.RESOLVED and issue.resolved_at is None:
                issue.resolved_at = timezone.now()
            issue.save(update_fields=["status", "resolved_at", "updated_at"])
        return Response(ReconciliationIssueSerializer(issue).data, status=status.HTTP_200_OK)


class ReconciliationRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id: int):
        connection = get_object_or_404(
            BrokerageConnection.objects.select_related("account__portfolio__profile"),
            id=connection_id,
            account__portfolio__profile__user=request.user,
        )
        try:
            async_mode = bool(request.data.get("async", False))
            if async_mode:
                job = AccountJobService.enqueue(
                    account=connection.account,
                    connection=connection,
                    job_type=AccountJob.JobType.RECONCILE,
                    payload={},
                    idempotency_key=f"reconcile:{connection.id}",
                )
                return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
            adapter = get_adapter(connection.provider)
            positions = adapter.fetch_positions(connection)
            summary = ReconciliationService.reconcile_positions(
                connection=connection,
                external_positions=[{"symbol": p.symbol, "quantity": str(p.quantity)} for p in positions],
            )
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(summary, status=status.HTTP_200_OK)


class PlaidWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        configured = (settings.PLAID_WEBHOOK_SECRET or "").strip()
        if configured:
            provided = (request.headers.get("X-Plaid-Webhook-Secret") or "").strip()
            if provided != configured:
                return Response({"detail": "Invalid webhook secret."}, status=status.HTTP_403_FORBIDDEN)

        item_id = request.data.get("item_id")
        webhook_type = request.data.get("webhook_type")
        webhook_code = request.data.get("webhook_code")

        if item_id:
            connection = BrokerageConnection.objects.filter(
                provider=BrokerageConnection.Provider.PLAID,
                external_account_id=item_id,
            ).select_related("account").first()
            if connection:
                connection.last_error = None
                connection.save(update_fields=["last_error", "updated_at"])
                AccountJobService.enqueue(
                    account=connection.account,
                    connection=connection,
                    job_type=AccountJob.JobType.SYNC_POSITIONS,
                    payload={"prune_missing": False},
                    idempotency_key=f"webhook_sync_positions:{connection.id}:{item_id}",
                )
                AccountJobService.enqueue(
                    account=connection.account,
                    connection=connection,
                    job_type=AccountJob.JobType.SYNC_TRANSACTIONS,
                    payload={"days": 30},
                    idempotency_key=f"webhook_sync_transactions:{connection.id}:{item_id}",
                )

        return Response(
            {
                "received": True,
                "webhook_type": webhook_type,
                "webhook_code": webhook_code,
                "item_id": item_id,
            },
            status=status.HTTP_200_OK,
        )


class JobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AccountJob.objects.filter(account__portfolio__profile__user=request.user).order_by("-created_at")
        return Response(JobSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class JobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id: int):
        job = get_object_or_404(
            AccountJob.objects.select_related("account__portfolio__profile"),
            id=job_id,
            account__portfolio__profile__user=request.user,
        )
        return Response(JobSerializer(job).data, status=status.HTTP_200_OK)
