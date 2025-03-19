from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from .serializers import PortfolioSerializer
from securities.serializers import StockPortfolioSerializer, SelfManagedAccountCreateSerializer

# Create your views here.


class PortfolioViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        profile = request.user.profile
        portfolio = profile.portfolio
        serializer = self.get_serializer(portfolio)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='stock-accounts')
    def stock_portfolio(self, request):
        """
        Get the user's stock portfolio.
        """
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='add-self-managed-account')
    def add_self_managed_account(self, request):
        """
        Adds a new SelfManagedAccount to the user's stock portfolio
        """
        # Get the user's profile and stock portfolio
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio

        # Deserialize data
        serializer = SelfManagedAccountCreateSerializer(
            data=request.data,
            # Pass stock_portfolio via context
            context={'stock_portfolio': stock_portfolio}
        )
        if serializer.is_valid():
            serializer.save()  # No need to pass stock_portfolio here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
