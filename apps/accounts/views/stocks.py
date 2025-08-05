from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import SelfManagedAccount, ManagedAccount
from accounts.permissions import IsAccountOwner
from accounts.services import (
    stock_account_service,
    stock_dashboard_service,
)
from accounts.serializers.stocks import (
    SelfManagedAccountSerializer,
    SelfManagedAccountCreateSerializer,
    ManagedAccountSerializer,
    ManagedAccountCreateSerializer,
)
from assets.serializers.stocks import StockHoldingCreateSerializer


class SelfManagedAccountListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SelfManagedAccountCreateSerializer

    def get_queryset(self):
        return stock_account_service.get_self_managed_accounts(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = stock_account_service.create_self_managed_account(
            request.user, serializer.validated_data
        )

        response_serializer = SelfManagedAccountSerializer(account)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class SelfManagedAccountDetailView(RetrieveAPIView):
    queryset = SelfManagedAccount.objects.all()
    serializer_class = SelfManagedAccountSerializer
    permission_classes = [IsAuthenticated, IsAccountOwner]


class ManagedAccountListCreateView(APIView):
    """
    GET: List all managed stock accounts for the user.
    POST: Create a new managed stock account.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = stock_account_service.get_managed_accounts(request.user)
        serializer = ManagedAccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ManagedAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = stock_account_service.create_managed_account(
            request.user, serializer.validated_data
        )
        return Response(
            ManagedAccountSerializer(account).data,
            status=status.HTTP_201_CREATED
        )


class ManagedAccountDetailView(RetrieveAPIView):
    queryset = ManagedAccount.objects.all()
    serializer_class = ManagedAccountSerializer
    permission_classes = [IsAuthenticated, IsAccountOwner]


class StockAccountsDashboardView(APIView):
    """
    GET: Returns a unified dashboard for all stock accounts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard_data = stock_dashboard_service.get_stock_accounts_dashboard(
            request.user)
        return Response(dashboard_data, status=status.HTTP_200_OK)


class AddHoldingView(CreateAPIView):
    serializer_class = StockHoldingCreateSerializer
    permission_classes = [IsAuthenticated, IsAccountOwner]

    def get_queryset(self):
        return SelfManagedAccount.objects.all()  # Required for permission checking

    def get_object(self):
        return SelfManagedAccount.objects.get(pk=self.kwargs['account_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['self_managed_account'] = self.get_object()
        return context

    def perform_create(self, serializer):
        serializer.save()


# class EditColumnValueView(APIView):
#     """
#     PATCH: Edit a column value for a specific stock holding.
#     """
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, value_id):
#         value_obj = holdings_service.edit_column_value(value_id, request.data, request.user)

#         return Response({
#             "id": value_obj.id,
#             "value": value_obj.value,
#             "is_edited": value_obj.is_edited
#         }, status=status.HTTP_200_OK)
