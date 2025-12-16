from rest_framework import generics
from subscriptions.models import AccountType
from subscriptions.serializers.account_type import AccountTypeSerializer


class AccountTypeListView(generics.ListAPIView):
    """
    Read-only API to list all available account types.
    """
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
