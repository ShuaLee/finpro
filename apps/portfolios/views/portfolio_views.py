"""
Portfolio Views
---------------

This module defines views for creating and retrieving the main Portfolio object.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from portfolios.serializers import PortfolioSerializer
from portfolios.services import portfolio_service
from users.models import Profile


class PortfolioCreateView(APIView):
    """
    API endpoint for creating a main Portfolio for a user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        try:
            portfolio = portfolio_service.create_portfolio(profile)
            serializer = PortfolioSerializer(portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
