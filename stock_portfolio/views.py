from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import StockPortfolio, SelfManagedAccount
from .serializers import StockPortfolioSerializer, SelfManagedAccountSerializer

# Create your views here.
class StockPortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio = request.user.profile.portfolio
        try:
            stock_portfolio = StockPortfolio.objects.get(portfolio=portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)
        
        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)
    
class SelfManagedAccountViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SelfManagedAccountSerializer

    def get_stock_portfolio(self):
        # grab the current user's Portfolio → StockPortfolio
        profile_portfolio = self.request.user.profile.portfolio
        # if you expect exactly one StockPortfolio per Portfolio:
        return get_object_or_404(StockPortfolio, portfolio=profile_portfolio)

    def get_queryset(self):
        sp = self.get_stock_portfolio()
        return SelfManagedAccount.objects.filter(stock_portfolio=sp)

    def perform_create(self, serializer):
        sp = self.get_stock_portfolio()
        serializer.save(stock_portfolio=sp)


class SelfManagedAccountCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        try:
            stock_portfolio = StockPortfolio.objects.get(portfolio=profile.portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)
        
        serializer = SelfManagedAccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(stock_portfolio=stock_portfolio)
            return Response(SelfManagedAccountSerializer(account).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)