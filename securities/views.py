from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import StockAccount
from .serializers import StockAccountSerializer, StockHoldingCreateSerializer
# Create your views here.


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
