from django.urls import path

from apps.integrations.views import (
    ActiveCommodityListView,
    ActiveCryptoListView,
    ActiveEquityListView,
    ActivePreciousMetalListView,
)

urlpatterns = [
    path("active-equities/", ActiveEquityListView.as_view(), name="active-equity-list"),
    path("active-cryptos/", ActiveCryptoListView.as_view(), name="active-crypto-list"),
    path("active-commodities/", ActiveCommodityListView.as_view(), name="active-commodity-list"),
    path("active-precious-metals/", ActivePreciousMetalListView.as_view(), name="active-precious-metal-list"),
]
