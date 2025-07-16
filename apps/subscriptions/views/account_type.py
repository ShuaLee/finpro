from rest_framework import generics
from apps.subscriptions.models import AccountType
from apps.subscriptions.serializers.account_type import AccountTypeSerializer


class AccountTypeListView(generics.ListAPIView):
    """
    Read-only API to list all available account types.
    """
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer