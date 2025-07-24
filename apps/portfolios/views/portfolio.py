"""
Portfolio Views
---------------

Provides endpoints for:
- Creating a main Portfolio for the authenticated user.
- Retrieving the user's existing Portfolio.
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from portfolios.serializers import PortfolioSerializer
from portfolios.services import portfolio_service
from users.models import Profile


class PortfolioCreateView(APIView):
    """
    Creates a main Portfolio for the authenticated user.

    Business rules:
    - Each profile can only have one portfolio.
    - Returns 400 if a portfolio already exists.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        if hasattr(profile, "portfolio"):
            return Response(
                {"error": "Portfolio already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        portfolio = portfolio_service.create_portfolio(profile)
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PortfolioDetailView(APIView):
    """
    Retrieves the authenticated user's Portfolio.
    Returns 404 if no portfolio exists.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        try:
            portfolio = profile.portfolio
        except ObjectDoesNotExist:
            return Response(
                {"error": "Portfolio not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data, status=status.HTTP_200_OK)
