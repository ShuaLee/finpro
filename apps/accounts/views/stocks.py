# accounts/views/stocks.py

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models.stocks import StockAccount
from accounts.permissions import IsAccountOwner
from accounts.services import stock_dashboard_service
from accounts.serializers.stocks import (
    StockAccountCreateSerializer,
    StockAccountDetailSerializer,
    StockAccountUpdateSerializer,
    StockAccountSwitchModeSerializer,
)
from assets.serializers.stocks import StockHoldingCreateSerializer


class StockAccountListCreateView(ListCreateAPIView):
    """
    GET /accounts/stocks/?mode=self_managed|managed
    POST /accounts/stocks/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StockAccountCreateSerializer  # for POST

    def get_queryset(self):
        # List the current user's accounts, optionally filtered by mode
        user = self.request.user
        qs = StockAccount.objects.filter(
            stock_portfolio=user.profile.portfolio.stockportfolio
        )
        mode = self.request.query_params.get("mode")
        if mode in {"self_managed", "managed"}:
            qs = qs.filter(account_mode=mode)
        return qs.select_related("stock_portfolio")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Use a read serializer for listing
        serializer = StockAccountDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = StockAccountCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(
            StockAccountDetailSerializer(account).data,
            status=status.HTTP_201_CREATED
        )


class StockAccountDetailView(RetrieveAPIView):
    """
    GET /accounts/stocks/<id>/
    """
    queryset = StockAccount.objects.all().select_related("stock_portfolio")
    serializer_class = StockAccountDetailSerializer
    permission_classes = [IsAuthenticated, IsAccountOwner]


class StockAccountPartialUpdateView(APIView):
    """
    PATCH /accounts/stocks/<id>/
    (Use for updating name/broker/currency/managed fields; NOT for switching modes.)
    """
    permission_classes = [IsAuthenticated, IsAccountOwner]

    def patch(self, request, pk):
        account = get_object_or_404(StockAccount, pk=pk)
        self.check_object_permissions(request, account)

        serializer = StockAccountUpdateSerializer(
            account, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(StockAccountDetailSerializer(account).data, status=200)


class StockAccountSwitchModeView(APIView):
    """
    POST /accounts/stocks/<id>/switch_mode/
    Body: {"new_mode": "self_managed"|"managed", "force": false}
    """
    permission_classes = [IsAuthenticated, IsAccountOwner]

    def post(self, request, pk):
        account = get_object_or_404(StockAccount, pk=pk)
        self.check_object_permissions(request, account)

        serializer = StockAccountSwitchModeSerializer(
            data=request.data, context={"account": account}
        )
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(StockAccountDetailSerializer(account).data, status=200)


class StockAccountsDashboardView(APIView):
    """
    GET /accounts/stocks/dashboard/
    Returns a unified dashboard for all stock accounts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = stock_dashboard_service.get_stock_accounts_dashboard(request.user)
        return Response(data, status=status.HTTP_200_OK)


class AddHoldingView(CreateAPIView):
    """
    POST /accounts/stocks/<account_id>/holdings/
    """
    serializer_class = StockHoldingCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountOwner]

    def get_queryset(self):
        # Needed for IsAccountOwner lookups
        return StockAccount.objects.all()

    def get_object(self):
        account = get_object_or_404(StockAccount, pk=self.kwargs['account_id'])
        return account

    def get_serializer_context(self):
        context = super().get_serializer_context()
        account = self.get_object()
        # Ensure only self-managed accounts can add holdings
        if account.account_mode != "self_managed":
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot add holdings to a managed account.")
        # If your StockHoldingCreateSerializer previously used 'self_managed_account',
        # update that serializer to read 'account' instead.
        context['account'] = account
        return context

    def perform_create(self, serializer):
        serializer.save()
