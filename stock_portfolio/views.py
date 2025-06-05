from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import StockPortfolio, SelfManagedAccount
from .serializers import StockPortfolioSerializer, SelfManagedAccountSerializer, SelfManagedAccountCreateSerializer, StockHoldingCreateSerializer

class StockPortfolioDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            stock_portfolio = StockPortfolio.objects.get(portfolio=request.user.profile.portfolio)
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

        holdings = account.holdings.select_related('stock').prefetch_related('column_values__column')
        for holding in holdings:
            row = {}
            for column in schema_columns:
                column_value = next(
                    (cv for cv in holding.column_values.all() if cv.column_id == column.id),
                    None
                )
                row[column.title] = column_value.get_value() if column_value else None
            holdings_data.append(row)
        
        return Response({
            'account_id': account.id,
            'account_name': account.name,
            'currency': account.currency,
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

        serializer = self.get_serializer(data=request.data, context={'self_managed_account': account})
        serializer.is_valid(raise_exception=True)
        holding = serializer.save()

        return Response(
            {'detail': f"Holding added for {holding.stock.ticker}", 'holding': StockHoldingCreateSerializer(holding).data},
            status=status.HTTP_201_CREATED
        )
    