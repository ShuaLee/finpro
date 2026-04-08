from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.serializers import (
    ActiveCommodityListingSerializer,
    ActiveCryptoListingSerializer,
    ActiveEquityListingSerializer,
    PreciousMetalListingSerializer,
)
from apps.integrations.services import MarketDataService
from apps.users.views.base import ServiceAPIView


class ActiveEquityListView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        queryset = MarketDataService.search_active_equities(query=query)[:25]
        return Response(ActiveEquityListingSerializer(queryset, many=True).data)


class ActiveCryptoListView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        queryset = MarketDataService.search_active_cryptos(query=query)[:25]
        return Response(ActiveCryptoListingSerializer(queryset, many=True).data)


class ActiveCommodityListView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        queryset = MarketDataService.search_active_commodities(query=query)[:25]
        return Response(ActiveCommodityListingSerializer(queryset, many=True).data)


class ActivePreciousMetalListView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = MarketDataService.get_active_precious_metals()
        return Response(PreciousMetalListingSerializer(rows, many=True).data)
