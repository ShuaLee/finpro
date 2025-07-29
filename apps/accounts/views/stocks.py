from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.services import (
    stock_account_service,
    holdings_service,
    stock_dashboard_service,
)

from accounts.serializers.stocks import (
    SelfManagedAccountSerializer,
    SelfManagedAccountCreateSerializer,
    ManagedAccountSerializer,
    ManagedAccountCreateSerializer,
)

# from assets.serializers.stocks import StockHoldingSerializer


class SelfManagedAccountListCreateView(APIView):
    """
    GET: List all self-managed stock accounts for the user.
    POST: Create a new self-managed stock account.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = stock_account_service.get_self_managed_accounts(
            request.user)
        serializer = SelfManagedAccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SelfManagedAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = stock_account_service.create_self_managed_account(
            request.user, serializer.validated_data
        )
        return Response(
            SelfManagedAccountSerializer(account).data,
            status=status.HTTP_201_CREATED
        )


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


class StockAccountsDashboardView(APIView):
    """
    GET: Returns a unified dashboard for all stock accounts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard_data = stock_dashboard_service.get_stock_accounts_dashboard(
            request.user)
        return Response(dashboard_data, status=status.HTTP_200_OK)


# class AddHoldingView(APIView):
#     """
#     POST: Add a new holding to a self-managed account.
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request, account_id):
#         context = {'self_managed_account': account_id}
#         holding = holdings_service.add_holding(account_id, request.data, context)

#         return Response({
#             "detail": "Holding added successfully",
#             "holding": StockHoldingSerializer(holding).data
#         }, status=status.HTTP_201_CREATED)


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
