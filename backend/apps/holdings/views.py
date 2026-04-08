from typing import Any, cast

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assets.models import Asset, AssetType
from apps.assets.services import AssetPriceService, AssetService
from apps.holdings.models import Container, Holding, HoldingFactDefinition, HoldingOverride, Portfolio
from apps.holdings.serializers import (
    ContainerCreateSerializer,
    ContainerSerializer,
    ContainerUpdateSerializer,
    HoldingFactDefinitionCreateSerializer,
    HoldingFactDefinitionSerializer,
    HoldingFactValueSerializer,
    HoldingFactValueUpsertSerializer,
    HoldingOverrideSerializer,
    HoldingOverrideUpsertSerializer,
    HoldingCreateSerializer,
    HoldingCreateWithAssetSerializer,
    HoldingSerializer,
    HoldingUpdateSerializer,
    PortfolioCreateSerializer,
    PortfolioSerializer,
    PortfolioUpdateSerializer,
)
from apps.holdings.services import ContainerService, HoldingService, HoldingValueService, PortfolioService
from apps.integrations.services import (
    ActiveCommodityAssetService,
    ActiveCryptoAssetService,
    ActiveEquityAssetService,
)
from apps.users.views.base import ServiceAPIView


def _hydrate_holding_asset_price(*, holding: Holding) -> Holding:
    asset = holding.asset
    market_data = getattr(asset, "market_data", None)
    if asset.owner is not None or market_data is None or not market_data.provider_symbol:
        return holding

    if asset.asset_type.slug not in {"equity", "crypto", "cryptocurrency", "commodity", "precious_metal"}:
        return holding

    AssetPriceService.get_current_price(asset=asset)
    holding.refresh_from_db()
    return holding


class PortfolioListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Portfolio.objects.filter(profile=request.user.profile).order_by("created_at", "id")

    def get(self, request):
        portfolios = self.get_queryset(request)
        return Response(PortfolioSerializer(portfolios, many=True).data)

    def post(self, request):
        serializer = PortfolioCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        portfolio = PortfolioService.create_portfolio(
            profile=request.user.profile,
            name=data["name"],
            kind=data.get("kind", Portfolio.Kind.PERSONAL),
            is_default=data.get("is_default", False),
        )
        return Response(PortfolioSerializer(portfolio).data, status=status.HTTP_201_CREATED)


class PortfolioDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Portfolio.objects.filter(profile=request.user.profile), pk=pk)

    def get(self, request, pk):
        portfolio = self.get_object(request, pk)
        return Response(PortfolioSerializer(portfolio).data)

    def patch(self, request, pk):
        portfolio = self.get_object(request, pk)
        serializer = PortfolioUpdateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        portfolio = PortfolioService.update_portfolio(
            portfolio=portfolio,
            profile=request.user.profile,
            name=data.get("name"),
            kind=data.get("kind"),
            is_default=data.get("is_default"),
        )
        return Response(PortfolioSerializer(portfolio).data)


class ContainerListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Container.objects.select_related("portfolio").filter(
            portfolio__profile=request.user.profile
        ).order_by("created_at", "id")

    def get(self, request):
        queryset = self.get_queryset(request)
        portfolio_id = request.query_params.get("portfolio")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        return Response(ContainerSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = ContainerCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        portfolio = get_object_or_404(
            Portfolio.objects.filter(profile=request.user.profile),
            pk=data["portfolio"].pk,
        )

        container = ContainerService.create_container(
            portfolio=portfolio,
            name=data["name"],
            kind=data.get("kind", ""),
            description=data.get("description", ""),
            is_tracked=data.get("is_tracked", False),
            source=data.get("source", ""),
            external_id=data.get("external_id", ""),
            external_parent_id=data.get("external_parent_id", ""),
        )
        return Response(ContainerSerializer(container).data, status=status.HTTP_201_CREATED)


class ContainerDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            Container.objects.select_related("portfolio").filter(portfolio__profile=request.user.profile),
            pk=pk,
        )

    def get(self, request, pk):
        container = self.get_object(request, pk)
        return Response(ContainerSerializer(container).data)

    def patch(self, request, pk):
        container = self.get_object(request, pk)
        serializer = ContainerUpdateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        container = ContainerService.update_container(
            container=container,
            profile=request.user.profile,
            name=data.get("name"),
            kind=data.get("kind"),
            description=data.get("description"),
            is_tracked=data.get("is_tracked"),
            source=data.get("source"),
            external_id=data.get("external_id"),
            external_parent_id=data.get("external_parent_id"),
            last_synced_at=data.get("last_synced_at"),
        )
        return Response(ContainerSerializer(container).data)


class HoldingListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Holding.objects.select_related(
            "container",
            "asset",
            "asset__price",
            "asset__market_data",
            "asset__dividend_snapshot",
        ).prefetch_related(
            "fact_values__definition",
            "overrides",
        ).filter(
            container__portfolio__profile=request.user.profile
        ).order_by("container_id", "asset_id", "id")

    def get(self, request):
        queryset = self.get_queryset(request)
        container_id = request.query_params.get("container")
        if container_id:
            queryset = queryset.filter(container_id=container_id)
        return Response(HoldingSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = HoldingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        container = get_object_or_404(
            Container.objects.filter(portfolio__profile=request.user.profile),
            pk=data["container"].pk,
        )
        asset = get_object_or_404(
            Asset.objects.filter(Q(owner__isnull=True) | Q(owner=request.user.profile)),
            pk=data["asset"].pk,
        )
        ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)

        holding = HoldingService.create_holding(
            container=container,
            asset=asset,
            quantity=data.get("quantity"),
            unit_value=data.get("unit_value"),
            unit_cost_basis=data.get("unit_cost_basis"),
            notes=data.get("notes", ""),
            data=data.get("data") or {},
        )
        return Response(HoldingSerializer(holding).data, status=status.HTTP_201_CREATED)


class HoldingCreateWithAssetView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HoldingCreateWithAssetSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        container = get_object_or_404(
            Container.objects.filter(portfolio__profile=request.user.profile),
            pk=data["container"].pk,
        )

        asset = data.get("asset")
        if asset is not None:
            asset = get_object_or_404(
                Asset.objects.filter(Q(owner__isnull=True) | Q(owner=request.user.profile)),
                pk=asset.pk,
            )
            ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)
        else:
            active_equity_symbol = data.get("active_equity_symbol")
            active_crypto_symbol = data.get("active_crypto_symbol")
            active_commodity_symbol = data.get("active_commodity_symbol")
            precious_metal_code = data.get("precious_metal_code")
            if active_equity_symbol:
                asset = ActiveEquityAssetService.get_or_create_public_asset(
                    symbol=active_equity_symbol,
                )
                ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)
            elif active_crypto_symbol:
                asset = ActiveCryptoAssetService.get_or_create_public_asset(
                    symbol=active_crypto_symbol,
                )
            elif active_commodity_symbol:
                asset = ActiveCommodityAssetService.get_or_create_public_asset(
                    symbol=active_commodity_symbol,
                )
            elif precious_metal_code:
                asset = ActiveCommodityAssetService.get_or_create_precious_metal_asset(
                    metal=precious_metal_code,
                )
            else:
                asset_type = get_object_or_404(
                    AssetType.objects.filter(Q(created_by__isnull=True) | Q(created_by=request.user.profile)),
                    pk=data["asset_type"].pk,
                )
                asset = AssetService.create_custom_asset(
                    profile=request.user.profile,
                    asset_type=asset_type,
                    name=data["asset_name"],
                    symbol=data.get("asset_symbol", ""),
                    description=data.get("asset_description", ""),
                    data=data.get("asset_data") or {},
                )

        holding = HoldingService.create_holding(
            container=container,
            asset=asset,
            quantity=data.get("quantity"),
            unit_value=data.get("unit_value"),
            unit_cost_basis=data.get("unit_cost_basis"),
            notes=data.get("notes", ""),
            data=data.get("data") or {},
        )
        return Response(HoldingSerializer(holding).data, status=status.HTTP_201_CREATED)


class HoldingDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            Holding.objects.select_related(
                "container",
                "asset",
                "asset__price",
                "asset__market_data",
                "asset__dividend_snapshot",
            ).prefetch_related(
                "fact_values__definition",
                "overrides",
            ).filter(
                container__portfolio__profile=request.user.profile
            ),
            pk=pk,
        )

    def get(self, request, pk):
        holding = self.get_object(request, pk)
        holding = _hydrate_holding_asset_price(holding=holding)
        return Response(HoldingSerializer(holding).data)

    def patch(self, request, pk):
        holding = self.get_object(request, pk)
        serializer = HoldingUpdateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        holding = HoldingService.update_holding(
            holding=holding,
            profile=request.user.profile,
            quantity=data.get("quantity"),
            unit_value=data.get("unit_value"),
            unit_cost_basis=data.get("unit_cost_basis"),
            notes=data.get("notes"),
            data=data.get("data"),
        )
        return Response(HoldingSerializer(holding).data)


class HoldingFactDefinitionListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return HoldingFactDefinition.objects.select_related("portfolio").filter(
            portfolio__profile=request.user.profile
        ).order_by("label", "key")

    def get(self, request):
        queryset = self.get_queryset(request)
        portfolio_id = request.query_params.get("portfolio")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        return Response(HoldingFactDefinitionSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = HoldingFactDefinitionCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        portfolio = get_object_or_404(
            Portfolio.objects.filter(profile=request.user.profile),
            pk=data["portfolio"].pk,
        )
        definition = HoldingValueService.create_fact_definition(
            portfolio=portfolio,
            key=data["key"],
            label=data["label"],
            data_type=data["data_type"],
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
        )
        return Response(HoldingFactDefinitionSerializer(definition).data, status=status.HTTP_201_CREATED)


class HoldingFactDefinitionDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            HoldingFactDefinition.objects.select_related("portfolio").filter(
                portfolio__profile=request.user.profile
            ),
            pk=pk,
        )

    def patch(self, request, pk):
        definition = self.get_object(request, pk)
        serializer = HoldingFactDefinitionCreateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        definition = HoldingValueService.update_fact_definition(
            definition=definition,
            profile=request.user.profile,
            label=data.get("label"),
            description=data.get("description"),
            data_type=data.get("data_type"),
            is_active=data.get("is_active"),
        )
        return Response(HoldingFactDefinitionSerializer(definition).data)

    def delete(self, request, pk):
        definition = self.get_object(request, pk)
        definition.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HoldingFactValueListUpsertView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_holding(self, request, pk):
        return get_object_or_404(
            Holding.objects.select_related("container", "container__portfolio").prefetch_related("fact_values__definition").filter(
                container__portfolio__profile=request.user.profile
            ),
            pk=pk,
        )

    def get(self, request, pk):
        holding = self.get_holding(request, pk)
        return Response(HoldingFactValueSerializer(holding.fact_values.all(), many=True).data)

    def post(self, request, pk):
        holding = self.get_holding(request, pk)
        serializer = HoldingFactValueUpsertSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        definition = get_object_or_404(
            HoldingFactDefinition.objects.filter(portfolio=holding.container.portfolio),
            pk=data["definition"].pk,
        )
        fact_value = HoldingValueService.upsert_fact_value(
            holding=holding,
            definition=definition,
            value=data.get("value"),
        )
        fact_value.refresh_from_db()
        return Response(HoldingFactValueSerializer(fact_value).data, status=status.HTTP_201_CREATED)


class HoldingOverrideListUpsertView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_holding(self, request, pk):
        return get_object_or_404(
            Holding.objects.select_related("container", "container__portfolio").prefetch_related("overrides").filter(
                container__portfolio__profile=request.user.profile
            ),
            pk=pk,
        )

    def get(self, request, pk):
        holding = self.get_holding(request, pk)
        return Response(HoldingOverrideSerializer(holding.overrides.all(), many=True).data)

    def post(self, request, pk):
        holding = self.get_holding(request, pk)
        serializer = HoldingOverrideUpsertSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        override = HoldingValueService.upsert_override(
            holding=holding,
            key=data["key"],
            data_type=data["data_type"],
            value=data.get("value"),
        )
        return Response(HoldingOverrideSerializer(override).data, status=status.HTTP_201_CREATED)


class HoldingOverrideDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, override_id):
        return get_object_or_404(
            HoldingOverride.objects.select_related("holding", "holding__container", "holding__container__portfolio").filter(
                holding__container__portfolio__profile=request.user.profile
            ),
            pk=override_id,
        )

    def delete(self, request, override_id):
        override = self.get_object(request, override_id)
        override.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
