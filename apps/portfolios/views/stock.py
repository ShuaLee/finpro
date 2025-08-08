"""
Stock Portfolio Views
----------------------

Endpoints for managing stock-specific portfolios.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# UPDATED imports: single model + unified serializer
from accounts.models.stocks import StockAccount
from accounts.serializers.stocks import StockAccountBaseSerializer

from portfolios.serializers.stock import StockPortfolioSerializer
from portfolios.services import stock_service, portfolio_service
from users.models import Profile


def _to_float(val):
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


class StockPortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio = getattr(request.user.profile, 'portfolio', None)
        if not portfolio:
            return Response({"detail": "Portfolio not found."}, status=status.HTTP_404_NOT_FOUND)

        stock_portfolio = getattr(portfolio, 'stockportfolio', None)
        if not stock_portfolio:
            return Response({"detail": "You haven't created a Stock Portfolio yet."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch accounts by mode from unified model
        base_qs = (
            StockAccount.objects
            .filter(stock_portfolio=stock_portfolio)
            .select_related(
                "stock_portfolio",
                "stock_portfolio__portfolio",
                "stock_portfolio__portfolio__profile",
            )
        )

        self_accounts = base_qs.filter(account_mode="self_managed")
        managed_accounts = base_qs.filter(account_mode="managed")

        # Compute totals using the model helper to value in profile FX
        self_total = sum(_to_float(a.get_value_in_profile_currency()) for a in self_accounts)
        managed_total = sum(_to_float(a.get_value_in_profile_currency()) for a in managed_accounts)
        grand_total = round(self_total + managed_total, 2)

        return Response({
            "summary": {
                "self_managed_total": round(self_total, 2),
                "managed_total": round(managed_total, 2),
                "grand_total": grand_total,
                "account_count": self_accounts.count() + managed_accounts.count(),
            },
            "self_managed_accounts": StockAccountBaseSerializer(self_accounts, many=True).data,
            "managed_accounts": StockAccountBaseSerializer(managed_accounts, many=True).data,
        }, status=status.HTTP_200_OK)


class StockPortfolioCreateView(APIView):
    """
    API endpoint for creating a StockPortfolio under the user's main Portfolio.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        try:
            portfolio = portfolio_service.get_portfolio(profile)
            stock_portfolio = stock_service.create_stock_portfolio(portfolio)
            # If you also want to initialize schema here, uncomment the next line:
            # stock_service.initialize_stock_schema(stock_portfolio)
            serializer = StockPortfolioSerializer(stock_portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
