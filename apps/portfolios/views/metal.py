"""
Metal Portfolio Views
----------------------

Endpoints for managing metal-specific portfolios.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.portfolios.serializers.metal import MetalPortfolioSerializer
from portfolios.services import metal_service, portfolio_service
from portfolios.permissions import IsPortfolioOwner
from users.models import Profile


class MetalPortfolioCreateView(APIView):
    """
    API endpoint for creating a MetalPortfolio under the user's main Portfolio.
    """
    permission_classes = [IsAuthenticated, IsPortfolioOwner]

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        try:
            portfolio = portfolio_service.get_portfolio(profile)
            metal_portfolio = metal_service.create_metal_portfolio(portfolio)
            serializer = MetalPortfolioSerializer(metal_portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
