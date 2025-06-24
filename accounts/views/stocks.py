from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.serializers.stocks import SelfManagedAccountSerializer
from assets.serializers.stocks import StockHoldingCreateSerializer
from schemas.models.stocks import StockPortfolioSCV
from schemas.serializers.stocks import StockPortfolioSCVEditSerializer
from models.stocks import SelfManagedAccount, ManagedAccount
from serializers.stocks import SelfManagedAccountCreateSerializer, ManagedAccountSerializer



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
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().select_related('active_schema').prefetch_related(
            'holdings__stock',
            'holdings__column_values__column'
        )

        accounts_data = []
        total_value = 0

        for account in queryset:
            schema = account.active_schema
            if not schema:
                continue

            schema_columns = schema.columns.all()
            holdings_data = []

            for holding in account.holdings.all():
                row = {}
                for column in schema_columns:
                    column_value = next(
                        (cv for cv in holding.column_values.all()
                        if cv.column_id == column.id),
                        None
                    )
                    row[column.title] = column_value.get_value() if column_value else None
                holdings_data.append(row)

            value = float(account.get_current_value_in_profile_fx() or 0)
            total_value += value

            accounts_data.append({
                'account_id': account.id,
                'account_name': account.name,
                'schema_name': schema.name,
                'current_value_fx': value,
                'columns': [col.title for col in schema_columns],
                'holdings': holdings_data,
            })

        return Response({
            'total_current_value_in_profile_fx': round(total_value, 2),
            'accounts': accounts_data
        })
    
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

        return Response({
            'account_id': account.id,
            'account_name': account.name,
            'schema_name': schema.name,
            'current_value_fx': float(account.get_total_current_value_in_profile_fx() or 0),
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
            value_obj = StockPortfolioSCV.objects.get(
                pk=value_id,
                holding__self_managed_account__id=pk,
                holding__self_managed_account__stock_portfolio__portfolio=request.user.profile.portfolio
            )
        except StockPortfolioSCV.DoesNotExist:
            return Response({"detail": "Column value not found or unauthorized."}, status=404)

        serializer = StockPortfolioSCVEditSerializer(
            value_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        updated_instance = serializer.save()
        return Response({
            "id": updated_instance.id,
            "value": updated_instance.get_value(),
        }, status=status.HTTP_200_OK)


class ManagedAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ManagedAccountSerializer

    def get_queryset(self):
        return ManagedAccount.objects.filter(
            stock_portfolio__portfolio=self.request.user.profile.portfolio
        )

