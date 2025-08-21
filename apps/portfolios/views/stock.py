# """
# Stock Portfolio Views
# ----------------------

# Endpoints for managing stock-specific portfolios.
# """

# from django.core.exceptions import ValidationError
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from accounts.models import SelfManagedAccount, ManagedAccount
# from accounts.serializers import SelfManagedAccountSerializer, ManagedAccountSerializer
# from apps.portfolios.services import sub_portfolio_creation
# from portfolios.serializers.stock import StockPortfolioSerializer
# from apps.portfolios.services import portfolio_management
# from users.models import Profile
# from decimal import Decimal


# class StockPortfolioDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         portfolio = getattr(request.user.profile, 'portfolio', None)
#         if not portfolio:
#             return Response({"detail": "Portfolio not found."}, status=status.HTTP_404_NOT_FOUND)

#         stock_portfolio = getattr(portfolio, 'stockportfolio', None)
#         if not stock_portfolio:
#             return Response({"detail": "You haven't created a Stock Portfolio yet."}, status=status.HTTP_404_NOT_FOUND)

#         # Fetch accounts
#         self_accounts = SelfManagedAccount.objects.filter(
#             stock_portfolio=stock_portfolio)
#         managed_accounts = ManagedAccount.objects.filter(
#             stock_portfolio=stock_portfolio)

#         # Use StockPortfolio methods
#         self_total = stock_portfolio.get_self_managed_total_pfx()
#         managed_total = stock_portfolio.get_managed_total_pfx()
#         grand_total = stock_portfolio.get_total_value_pfx()

#         return Response({
#             "summary": {
#                 "self_managed_total": self_total,
#                 "managed_total": managed_total,
#                 "grand_total": grand_total,
#                 "account_count": self_accounts.count() + managed_accounts.count()
#             },
#             "self_managed_accounts": SelfManagedAccountSerializer(self_accounts, many=True).data,
#             "managed_accounts": ManagedAccountSerializer(managed_accounts, many=True).data
#         }, status=status.HTTP_200_OK)


# class StockPortfolioCreateView(APIView):
#     """
#     API endpoint for creating a StockPortfolio under the user's main Portfolio.
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         profile = Profile.objects.get(user=request.user)
#         try:
#             portfolio = portfolio_management.get_portfolio(profile)
#             stock_portfolio = sub_portfolio_creation.create_stock_portfolio(
#                 portfolio)
#             serializer = StockPortfolioSerializer(stock_portfolio)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         """
#             # Optionally initialize schema
#             stock_service.initialize_stock_schema(stock_portfolio)
#             serializer = StockPortfolioSerializer(stock_portfolio)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         """
