from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from .models import StockPortfolio, SelfManagedAccount, StockHolding
from .serializers import (
    StockHoldingCreateSerializer, StockPortfolioSerializer, SelfManagedAccountCreateSerializer,
    SelfManagedAccountSerializer, StockHoldingSerializer, StockHoldingUpdateSerializer
)
import logging

logger = logging.getLogger(__name__)


class StockPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StockPortfolio.objects.filter(portfolio__profile__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            logger.error(f"No StockPortfolio found for user: {request.user}")
            return Response({"detail": "Stock portfolio not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        stock_portfolio = queryset.first()
        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        # For /stock-accounts/, lists all stock accounts
        queryset = self.get_queryset()
        if not queryset.exists():
            logger.error(f"No StockPortfolio found for user: {request.user}")
            return Response({"detail": "Stock portfolio not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        stock_portfolio = queryset.first()
        # Combine all account types (currently only SelfManagedAccount)
        self_managed = stock_portfolio.self_managed_accounts.all()
        # Add managed_accounts when implemented: managed = stock_portfolio.managed_accounts.all()
        # Extend with managed_accounts later: + list(managed)
        accounts = list(self_managed)
        # Update serializer for polymorphism later
        serializer = SelfManagedAccountSerializer(accounts, many=True)
        logger.debug(f"Serialized accounts: {serializer.data}")
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='add-self-managed-account')
    def add_self_managed_account(self, request, pk=None):
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        serializer = SelfManagedAccountCreateSerializer(
            data=request.data,
            context={'stock_portfolio': stock_portfolio}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = StockPortfolioUpdateSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StockPortfolioSerializer(instance).data)


class SelfManagedAccountViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SelfManagedAccountCreateSerializer
        elif self.action == 'add_stock':
            return StockHoldingCreateSerializer
        elif self.action == 'update_stock' or self.action == 'reset_stock_column':
            return StockHoldingUpdateSerializer
        return SelfManagedAccountSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        return SelfManagedAccount.objects.filter(stock_portfolio=stock_portfolio)

    def create(self, request, *args, **kwargs):
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        serializer = self.get_serializer(data=request.data, context={
                                         'stock_portfolio': stock_portfolio})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='add-stock')
    def add_stock(self, request, pk=None):
        account = self.get_object()
        serializer = StockHoldingCreateSerializer(
            data=request.data, context={'stock_account': account}
        )
        serializer.is_valid(raise_exception=True)
        holding = serializer.save()
        response_serializer = StockHoldingSerializer(holding)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'], url_path='update-stock/(?P<holding_pk>[^/.]+)')
    def update_stock(self, request, pk=None, holding_pk=None):
        account = self.get_object()
        try:
            holding = StockHolding.objects.get(
                stock_account=account, pk=holding_pk)
        except StockHolding.DoesNotExist:
            return Response({"error": "Stock holding not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StockHoldingUpdateSerializer(
            holding, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StockHoldingSerializer(holding).data)

    @action(detail=True, methods=['POST'], url_path='reset-stock-column/(?P<holding_pk>[^/.]+)')
    def reset_stock_column(self, request, pk=None, holding_pk=None):
        account = self.get_object()
        try:
            holding = StockHolding.objects.get(
                stock_account=account, pk=holding_pk)
        except StockHolding.DoesNotExist:
            return Response({"error": "Stock holding not found"}, status=status.HTTP_404_NOT_FOUND)
        column_name = request.data.get('column_name')
        if column_name in account.stock_portfolio.custom_columns:
            holding.custom_data.pop(column_name, None)
            holding.save()
            return Response(StockHoldingSerializer(holding).data)
        return Response({"error": "Invalid column name"}, status=status.HTTP_400_BAD_REQUEST)
