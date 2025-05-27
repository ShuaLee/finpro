from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import StockPortfolio, SelfManagedAccount
from .serializers import StockPortfolioSerializer, SelfManagedAccountSerializer, SelfManagedAccountCreateSerializer, StockHoldingCreateSerializer

class AddStockHoldingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        account = get_object_or_404(SelfManagedAccount, pk=pk)

        if account.stock_portfolio.portfolio.profile != request.user.profile:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StockHoldingCreateSerializer(data=request.data, context={'self_managed_account': account})
        serializer.is_valid(raise_exception=True)
        holding = serializer.save()
        return Response({'detail': f"Holding added: {holding}"}, status=status.HTTP_201_CREATED)

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