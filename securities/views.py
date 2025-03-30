from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from .models import StockPortfolio, SelfManagedAccount, StockHolding
from .serializers import StockHoldingCreateSerializer, StockPortfolioSerializer, SelfManagedAccountCreateSerializer, SelfManagedAccountSerializer, StockHoldingSerializer


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

    @action(detail=False, methods=['POST'], url_path='add-self-managed-account')
    def add_self_managed_account(self, request, pk=None):
        """
        Add a self managed account to the user's StockPortfolio.
        """
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio

        # Pass stock_portfolio to serializer context
        serializer = SelfManagedAccountCreateSerializer(
            data=request.data,
            context={'stock_portfolio': stock_portfolio}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)


class SelfManagedAccountViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SelfManagedAccountCreateSerializer
        elif self.action == 'add_stock':
            return StockHoldingCreateSerializer
        return SelfManagedAccountSerializer

    def get_queryset(self):
        # Filter to the user's stock portfolio
        profile = self.request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        return SelfManagedAccount.objects.filter(stock_portfolio=stock_portfolio)

    def create(self, request, *args, **kwargs):
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stock_portfolio
        serializer = self.get_serializer(data=request.data, context={
                                         'stock_portfolio': stock_portfolio})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        # Gets the SelfManagedAccount by pk, scoped to the user's stock_portfolio
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='add-stock')
    def add_stock(self, request, pk=None):
        account = self.get_object()  # SelfManagedAccount instance
        serializer = StockHoldingCreateSerializer(
            data=request.data, context={'stock_account': account}
        )
        serializer.is_valid(raise_exception=True)

        # Create the holding (always a StockHolding instance)
        holding = serializer.create(serializer.validated_data)

        # Serialize with StockHoldingSerializer (only one type now)
        response_serializer = StockHoldingSerializer(holding)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
