from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.serializers import ActiveEquityListingSerializer
from apps.integrations.services import MarketDataService
from apps.users.views.base import ServiceAPIView


class ActiveEquityListView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        queryset = MarketDataService.search_active_equities(query=query)[:25]
        return Response(ActiveEquityListingSerializer(queryset, many=True).data)
