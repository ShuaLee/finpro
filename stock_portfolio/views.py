from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import StockPortfolio, SelfManagedAccount, StockPortfolioSchemaColumnValue
from .serializers import StockPortfolioSerializer, SelfManagedAccountSerializer, SelfManagedAccountCreateSerializer, StockHoldingCreateSerializer, StockPortfolioSchemaColumnValueEditSerializer


class StockPortfolioDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            stock_portfolio = StockPortfolio.objects.get(
                portfolio=request.user.profile.portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)

        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)


class SelfManagedAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SelfManagedAccount.objects.filter(
            stock_portfolio__portfolio=self.request.user.profile.portfolio
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return SelfManagedAccountCreateSerializer
        if self.action == 'add_holding':
            return StockHoldingCreateSerializer
        return SelfManagedAccountSerializer

    def retrieve(self, request, pk=None):
        account = self.get_object()

        if account.stock_portfolio.portfolio.profile != request.user.profile:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

        schema = account.active_schema
        if not schema:
            return Response({"detail": "No active schema set."}, status=400)

        schema_columns = schema.columns.all()
        holdings_data = []

        holdings = account.holdings.select_related(
            'stock').prefetch_related('column_values__column')
        for holding in holdings:
            row = {}
            for column in schema_columns:
                column_value = next(
                    (cv for cv in holding.column_values.all()
                     if cv.column_id == column.id),
                    None
                )
                row[column.title] = column_value.get_value(
                ) if column_value else None
            holdings_data.append(row)

        total_fx_value = 0
        for holding in holdings:
            val = holding.get_column_value('value_in_profile_fx')
            print(f"Value for {holding}: {val}")
            if val is not None:
                total_fx_value += float(val)

        return Response({
            'account_id': account.id,
            'account_name': account.name,
            'schema_name': schema.name,
            'columns': [col.title for col in schema_columns],
            'holdings': holdings_data,
        })

    @action(detail=True, methods=['post'], url_path='add-holding')
    def add_holding(self, request, pk=None):
        account = self.get_object()

        # Ensure account belongs to the requesting user
        if account.stock_portfolio.portfolio.profile != request.user.profile:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data, context={
                                         'self_managed_account': account})
        serializer.is_valid(raise_exception=True)
        try:
            holding = serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)

        return Response(
            {'detail': f"Holding added for {holding.stock.ticker}",
                'holding': StockHoldingCreateSerializer(holding).data},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get', 'patch'], url_path='edit-column-value/(?P<value_id>[^/.]+)')
    def edit_column_value(self, request, pk=None, value_id=None):
        try:
            value_obj = StockPortfolioSchemaColumnValue.objects.get(
                pk=value_id,
                holding__self_managed_account__id=pk,
                holding__self_managed_account__stock_portfolio__portfolio=request.user.profile.portfolio
            )
        except StockPortfolioSchemaColumnValue.DoesNotExist:
            return Response({"detail": "Column value not found or unauthorized."}, status=404)

        serializer = StockPortfolioSchemaColumnValueEditSerializer(
            value_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        updated_instance = serializer.save()
        return Response({
            "id": updated_instance.id,
            "value": updated_instance.get_value(),
        }, status=status.HTTP_200_OK)
