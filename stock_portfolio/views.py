from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import StockPortfolio, SelfManagedAccount, SchemaColumnValue
from .serializers import StockPortfolioSerializer, SelfManagedAccountSerializer, SchemaColumnValueSerializer
import logging
# Create your views here.

logger = logging.getLogger(__name__)


class StockPortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio = request.user.profile.portfolio
        try:
            stock_portfolio = StockPortfolio.objects.get(portfolio=portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)

        serializer = StockPortfolioSerializer(stock_portfolio)
        return Response(serializer.data)


class SelfManagedAccountViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SelfManagedAccountSerializer

    def get_stock_portfolio(self):
        profile_portfolio = self.request.user.profile.portfolio
        return get_object_or_404(StockPortfolio, portfolio=profile_portfolio)

    def get_queryset(self):
        sp = self.get_stock_portfolio()
        return SelfManagedAccount.objects.filter(stock_portfolio=sp)

    def perform_create(self, serializer):
        sp = self.get_stock_portfolio()
        serializer.save(stock_portfolio=sp)

    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action in ['update_schema_column_value', 'reset_schema_column_value']:
            logger.debug(
                f"Using SchemaColumnValueSerializer for action={self.action}")
            return SchemaColumnValueSerializer
        logger.debug(
            f"Using SelfManagedAccountSerializer for action={self.action}")
        return super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        """Ensure the correct serializer is used for all contexts."""
        serializer_class = self.get_serializer_class()
        logger.debug(
            f"get_serializer: action={self.action}, serializer_class={serializer_class.__name__}")
        return serializer_class(*args, **kwargs)

    @action(detail=True, methods=['get', 'patch'], url_path='schema-column-values/(?P<value_id>\d+)')
    def update_schema_column_value(self, request, pk=None, value_id=None):
        """Retrieve or update a SchemaColumnValue."""
        account = self.get_object()
        try:
            column_value = SchemaColumnValue.objects.get(
                id=value_id,
                stock_holding__stock_account=account
            )
        except SchemaColumnValue.DoesNotExist:
            return Response({"detail": "SchemaColumnValue not found."}, status=404)

        if request.method == 'GET':
            serializer = SchemaColumnValueSerializer(column_value)
            logger.debug(
                f"GET SchemaColumnValue {value_id}, value={serializer.data['value']}, is_edited={serializer.data['is_edited']}")
            return Response(serializer.data)

        serializer = SchemaColumnValueSerializer(
            column_value, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Use serializer.data to ensure consistent response
            response_data = {
                'id': column_value.id,
                'value': column_value.value,
                'is_edited': column_value.is_edited
            }
            logger.debug(
                f"PATCH SchemaColumnValue {value_id}, response={response_data}")
            return Response(response_data)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'], url_path='schema-column-values/(?P<value_id>\d+)/reset')
    def reset_schema_column_value(self, request, pk=None, value_id=None):
        """Reset a SchemaColumnValue to its default value."""
        account = self.get_object()
        try:
            column_value = SchemaColumnValue.objects.get(
                id=value_id,
                stock_holding__stock_account=account
            )
        except SchemaColumnValue.DoesNotExist:
            return Response({"detail": "SchemaColumnValue not found."}, status=404)

        column_value.reset_to_default()
        response_data = {
            'id': column_value.id,
            'value': column_value.value,
            'is_edited': column_value.is_edited
        }
        logger.debug(
            f"Reset SchemaColumnValue {value_id}, response={response_data}")
        return Response(response_data)


@action(detail=True, methods=['post'], url_path='schema-column-values/(?P<value_id>\d+)/reset')
def reset_schema_column_value(self, request, pk=None, value_id=None):
    """Reset a SchemaColumnValue to its default value."""
    account = self.get_object()
    try:
        column_value = SchemaColumnValue.objects.get(
            id=value_id,
            stock_holding__stock_account=account
        )
    except SchemaColumnValue.DoesNotExist:
        return Response({"detail": "SchemaColumnValue not found."}, status=404)

    column_value.reset_to_default()
    return Response({
        'id': column_value.id,
        'value': column_value.value,
        'is_edited': column_value.is_edited
    })


class SelfManagedAccountCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        try:
            stock_portfolio = StockPortfolio.objects.get(
                portfolio=profile.portfolio)
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)

        serializer = SelfManagedAccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(stock_portfolio=stock_portfolio)
            return Response(SelfManagedAccountSerializer(account).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SchemaColumnValueViewSet(ModelViewSet):
    queryset = SchemaColumnValue.objects.all()
    serializer_class = SchemaColumnValueSerializer

    def get_queryset(self):
        # Assuming `self.kwargs['account_pk']` provides the primary key for the SelfManagedAccount
        account_pk = self.kwargs['account_pk']

        return SchemaColumnValue.objects.filter(
            stock_holding__account__self_managed_account__id=account_pk,
            stock_holding__account__stock_portfolio__portfolio=self.request.user.profile.portfolio
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update the value of SchemaColumnValue
        updated_value = serializer.save()

        return Response({
            'id': updated_value.id,
            'value': updated_value.value
        })

    @action(detail=True, methods=['POST'])
    def reset_to_default(self, request, pk=None):
        column_value = self.get_object()
        column_value.reset_to_default()

        return Response({
            'id': column_value.id,
            'value': column_value.value
        })


class SchemaColumnValueUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        column_value = get_object_or_404(SchemaColumnValue, pk=pk)
        serializer = SchemaColumnValueSerializer(
            column_value, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
