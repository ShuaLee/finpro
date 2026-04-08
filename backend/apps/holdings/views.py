from typing import Any, cast

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assets.models import Asset, AssetType
from apps.assets.services import AssetService
from apps.holdings.models import Container, Holding, Portfolio
from apps.holdings.serializers import (
    ContainerCreateSerializer,
    ContainerSerializer,
    ContainerUpdateSerializer,
    HoldingCreateSerializer,
    HoldingCreateWithAssetSerializer,
    HoldingSerializer,
    HoldingUpdateSerializer,
    PortfolioCreateSerializer,
    PortfolioSerializer,
    PortfolioUpdateSerializer,
)
from apps.holdings.services import ContainerService, HoldingService, PortfolioService
from apps.integrations.services import (
    ActiveCommodityAssetService,
    ActiveCryptoAssetService,
    ActiveEquityAssetService,
)
from apps.users.views.base import ServiceAPIView


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
        return Holding.objects.select_related("container", "asset").filter(
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
            Holding.objects.select_related("container", "asset").filter(
                container__portfolio__profile=request.user.profile
            ),
            pk=pk,
        )

    def get(self, request, pk):
        holding = self.get_object(request, pk)
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
