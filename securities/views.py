from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from .models import StockPortfolio, SelfManagedAccount, StockHolding, StockPortfolioSchema, SchemaColumn
from .serializers import (
    StockHoldingCreateSerializer, StockPortfolioSerializer, SelfManagedAccountCreateSerializer,
    SelfManagedAccountSerializer, StockHoldingSerializer, StockHoldingUpdateSerializer, StockPortfolioSchemaSerializer, SchemaColumnAddSerializer
)
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
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

    @action(detail=True, methods=['DELETE'], url_path='remove-stock/(?P<holding_pk>[^/.]+)')
    def remove_stock(self, request, pk=None, holding_pk=None):
        account = self.get_object()
        try:
            holding = StockHolding.objects.get(
                stock_account=account, pk=holding_pk)
            holding.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except StockHolding.DoesNotExist:
            return Response({"error": "Stock holding not found"}, status=status.HTTP_404_NOT_FOUND)

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


class StockPortfolioSchemaViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSchemaSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'add_column':
            return SchemaColumnAddSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """
        Return schemas ties to the authenticated user's StockPortfolio.
        """
        profile = self.request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        return StockPortfolioSchema.objects.filter(stock_portfolio=stock_portfolio)

    def get_stock_portfolio(self):
        profile = self.request.user.profile
        portfolio = profile.portfolio
        return get_object_or_404(StockPortfolio, portfolio=portfolio)

    def perform_create(self, serializer):
        """
        Create a new schema tied to the user's Stock Portfolio.
        """
        stock_portfolio = self.get_stock_portfolio()
        serializer.save(stock_portfolio=stock_portfolio)

    def perform_update(self, serializer):
        # Handle updates (e.g., PATCH to change is_active)
        try:
            serializer.save()
        except ValidationError as e:
            raise DRFValidationError({"detail": str(e)})

    def perform_destroy(self, instance):
        """
        Prevent deletion of non-deletable schemas and ensure an active schema remains.
        """
        if not instance.is_deletable:
            raise PermissionDenied(
                "Cannot delete a non-deletable schema like 'Basic'.")
        if instance.is_active and instance.stock_portfolio.schemas.count() > 1:
            next_schema = instance.stock_portfolio.schemas.exclude(
                id=instance.id).first()
            next_schema.is_active = True
            next_schema.save()
        instance.delete()

    @action(detail=True, methods=['post'], url_path='add-column', serializer_class=SchemaColumnAddSerializer)
    def add_column(self, request, pk=None):
        schema = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            title = serializer.validated_data['title']
            column_type = serializer.validated_data['column_type']
            source = serializer.validated_data.get('source', None)
            editable = serializer.validated_data.get('editable', True)

            # 🔄 Automatically determine value_type based on source
            if source:
                value_type = SchemaColumn.SOURCE_VALUE_TYPE_MAP.get(
                    source, 'text')  # fallback to 'text'
            else:
                # Use column_type-based fallback
                if column_type in ('custom', 'calculated'):
                    value_type = 'text'  # or let user define it manually if you expose it
                else:
                    value_type = 'number'

            column, created = SchemaColumn.objects.get_or_create(
                schema=schema,
                title=title,
                defaults={
                    'source': source,
                    'editable': editable,
                    'column_type': column_type,
                }
            )

            if not created:
                return Response(
                    {"error": "Column with this title already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Sync holdings
            for account in schema.stock_portfolio.self_managed_accounts.all():
                for holding in account.stockholding_set.all():
                    holding.sync_values()

            return Response({
                "message": "Column added successfully.",
                "column": {
                    "title": title,
                    "column_type": column_type,
                    "source": source,
                    "editable": editable,
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update-column')
    def update_column(self, request, pk=None):
        schema = self.get_object()
        title = request.data.get('title')
        source = request.data.get('source')
        editable = request.data.get('editable')
        column_type = request.data.get('column_type')

        if not title:
            return Response({"error": "Title is required to identify the column"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            column = SchemaColumn.objects.get(schema=schema, title=title)
        except SchemaColumn.DoesNotExist:
            return Response({"error": "Column not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update fields if provided
        if source is not None:
            column.source = source

            # 🔄 Automatically update value_type based on new source
            column.value_type = SchemaColumn.SOURCE_VALUE_TYPE_MAP.get(
                source, 'text')

        if editable is not None:
            column.editable = editable

        if column_type is not None:
            column.column_type = column_type

            # Fallback to type-based value_type if no source provided
            if not source:
                if column_type in ('custom', 'calculated'):
                    column.value_type = 'text'
                else:
                    column.value_type = 'number'

        column.save()

        # Sync all holdings if the column definition changed
        for account in schema.stock_portfolio.self_managed_accounts.all():
            for holding in account.stockholding_set.all():
                holding.sync_values()

        return Response({"message": "Column updated", "column": {"title": column.title, "source": column.source, "editable": column.editable, "value_type": column.value_type, "column_type": column.column_type}}, status=status.HTTP_200_OK)
