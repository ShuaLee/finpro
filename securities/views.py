from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StockPortfolio
from .serializers import StockHoldingCreateSerializer, StockPortfolioSerializer


# Create your views here.
class StockPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def me(self, request):
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
