from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import StockAccount, StockPortfolio
from .serializers import StockAccountSerializer, StockHoldingCreateSerializer, StockPortfolioSerializer
# Create your views here.


class StockPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return StockPortfolio.objects.filter(portfolio__profile_id=profile_id)

    def get_object(self):
        """
        Retrieve the single StockPortfolio for the profile's IndividualPortfolio.
        """
        profile_id = self.kwargs['profile_pk']
        return StockPortfolio.objects.get(portfolio__profile_id=profile_id)

    """
    THIS HASNT BEEN IMPLEMENTED CORRECTLY
    @action(detail=True, methods=['post'], url_path='add-stockaccount')
    def add_stockaccount(self, request, profile_pk=None):
        stock_portfolio = self.get_object()  # Get the StockPortfolio instance
        serializer = StockAccountSerializer(data=request.data, context={
                                            'stock_portfolio': stock_portfolio})
        if serializer.is_valid():
            serializer.save(stock_portfolio=stock_portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)"
    """


class StockAccountViewSet(viewsets.ModelViewSet):
    serializer_class = StockAccountSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return StockAccount.objects.filter(stock_portfolio__portfolio__profile_id=profile_id)

    @action(detail=True, methods=['post'], serializer_class=StockHoldingCreateSerializer, url_path='add-stock')
    def add_stock(self, request, profile_pk=None, pk=None):
        stock_account = self.get_object()
        serializer = self.get_serializer(data=request.data, context={
                                         'stock_account': stock_account})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
