from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import StockAccount, StockPortfolio
from .serializers import StockAccountSerializer, StockHoldingCreateSerializer, StockPortfolioSerializer
# Create your views here.


class StockPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSerializer

    def get_queryset(self):
        individual_portfolio_id = self.kwargs['portfolio_pk']
        return StockPortfolio.objects.filter(individual_portfolio_id=individual_portfolio_id)

    @action(detail=True, methods=['post'], url_path='reset-columns')
    def reset_columns(self, request, profile_pk=None, individual_portfolio_pk=None, pk=None):
        stock_portfolio = self.get_object()
        custom_columns = stock_portfolio.custom_columns
        for col in custom_columns:
            if custom_columns[col] and custom_columns[col].get('override'):
                custom_columns[col] = None
        stock_portfolio.custom_columns = custom_columns
        stock_portfolio.save()
        for account in stock_portfolio.stock_accounts.all():
            for holding in account.stockholding_set.all():
                holding.stock.update_from_yfinance()
        serializer = self.get_serializer(stock_portfolio)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StockAccountViewSet(viewsets.ModelViewSet):
    serializer_class = StockAccountSerializer

    def get_queryset(self):
        """
        Filter StockAccounts by the portfolio ID from the URL.
        """
        portfolio_id = self.kwargs['portfolio_pk']
        return StockAccount.objects.filter(portfolio_id=portfolio_id)

    @action(detail=True, methods=['post'], serializer_class=StockHoldingCreateSerializer, url_path='add-stock')
    def add_stock(self, request, profile_pk=None, portfolio_pk=None, pk=None):
        """
        Add stock to this StockAccount.
        """
        stock_account = self.get_object()  # Get the specific StockAccount instance
        serializer = self.get_serializer(data=request.data, context={
                                         'stock_account': stock_account})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
