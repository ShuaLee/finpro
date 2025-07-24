"""
Stock Portfolio Views
----------------------

Endpoints for managing stock-specific portfolios.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from portfolios.models.stock import StockPortfolio
from portfolios.permissions import IsPortfolioOwner
# from portfolios.services.stock_dashboard_service import get_stock_dashboard
from portfolios.serializers.stock import StockPortfolioSerializer
from portfolios.services import stock_service, portfolio_service
from users.models import Profile


class StockPortfolioCreateView(APIView):
    """
    API endpoint for creating a StockPortfolio under the user's main Portfolio.
    """

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        try:
            portfolio = portfolio_service.get_portfolio(profile)
            stock_portfolio = stock_service.create_stock_portfolio(portfolio)
            # Optionally initialize schema
            stock_service.initialize_stock_schema(stock_portfolio)
            serializer = StockPortfolioSerializer(stock_portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


"""
class StockPortfolioDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsPortfolioOwner]

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            stock_portfolio = StockPortfolio.objects.get(
                portfolio=profile.portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, stock_portfolio)

        dashboard_data = get_stock_dashboard(stock_portfolio)
        return Response(dashboard_data, status=status.HTTP_200_OK)
"""
