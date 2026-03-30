# """
# Portfolio Views
# ---------------

# Provides endpoints for:
# - Retrieving the user's existing Portfolio.
# """

# from django.core.exceptions import ObjectDoesNotExist
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from portfolios.serializers import PortfolioSerializer
# from users.models import Profile


# class PortfolioDetailView(APIView):
#     """
#     Retrieves the authenticated user's Portfolio.
#     Returns 404 if no portfolio exists (bootstrap guarantees it should).
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         profile = Profile.objects.get(user=request.user)
#         try:
#             portfolio = profile.portfolio
#         except ObjectDoesNotExist:
#             return Response(
#                 {"error": "Portfolio not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         has_stock = hasattr(portfolio, "stockportfolio") and portfolio.stockportfolio is not None
#         has_metal = hasattr(portfolio, "metalportfolio") and portfolio.metalportfolio is not None
#         has_crypto = hasattr(portfolio, "cryptoportfolio") and portfolio.cryptoportfolio is not None

#         data = PortfolioSerializer(portfolio).data

#         # Provide helpful creation endpoints for missing sub-portfolios
#         data["subportfolios"] = {
#             "has_stock_portfolio": bool(has_stock),
#             "has_metal_portfolio": bool(has_metal),
#             "create_urls": {
#                 "stock": reverse("create-stock-portfolio"),
#                 "metal": reverse("create-metal-portfolio"),
#             },
#         }

#         return Response(data, status=status.HTTP_200_OK)
