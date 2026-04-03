from typing import Any, cast

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assets.models import Asset, AssetType
from apps.assets.serializers import (
    AssetCreateSerializer,
    AssetPickerSerializer,
    AssetSerializer,
    AssetTypeCreateSerializer,
    AssetTypeSerializer,
    AssetTypeUpdateSerializer,
    AssetUpdateSerializer,
)
from apps.assets.services import AssetService, AssetTypeService
from apps.users.views.base import ServiceAPIView


class AssetTypeListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        asset_types = AssetTypeService.list_available_for_profile(profile=request.user.profile).order_by("name")
        return Response(AssetTypeSerializer(asset_types, many=True).data)

    def post(self, request):
        serializer = AssetTypeCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        asset_type = AssetTypeService.create_custom_asset_type(
            profile=request.user.profile,
            name=data["name"],
            description=data.get("description", ""),
        )
        return Response(AssetTypeSerializer(asset_type).data, status=status.HTTP_201_CREATED)


class AssetTypeDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            AssetType.objects.filter(Q(created_by__isnull=True) | Q(created_by=request.user.profile)),
            pk=pk,
        )

    def get(self, request, pk):
        asset_type = self.get_object(request, pk)
        return Response(AssetTypeSerializer(asset_type).data)

    def patch(self, request, pk):
        asset_type = self.get_object(request, pk)
        serializer = AssetTypeUpdateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        asset_type = AssetTypeService.update_custom_asset_type(
            asset_type=asset_type,
            profile=request.user.profile,
            name=data.get("name"),
            description=data.get("description"),
        )
        return Response(AssetTypeSerializer(asset_type).data)

    def delete(self, request, pk):
        asset_type = self.get_object(request, pk)
        AssetTypeService.delete_custom_asset_type(asset_type=asset_type, profile=request.user.profile)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssetListCreateView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = Asset.objects.select_related("asset_type", "owner__user").filter(
            Q(owner__isnull=True) | Q(owner=request.user.profile)
        )
        query = (request.query_params.get("q") or "").strip()
        asset_type_id = request.query_params.get("asset_type")
        owned_only = (request.query_params.get("owned_only") or "").strip().lower()
        active_only = (request.query_params.get("active_only") or "").strip().lower()

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(symbol__icontains=query))
        if asset_type_id:
            queryset = queryset.filter(asset_type_id=asset_type_id)
        if owned_only in {"1", "true", "yes"}:
            queryset = queryset.filter(owner=request.user.profile)
        if active_only in {"1", "true", "yes"}:
            queryset = queryset.filter(is_active=True)

        return queryset

    def get(self, request):
        assets = self.get_queryset(request).order_by("name", "symbol")
        return Response(AssetPickerSerializer(assets, many=True).data)

    def post(self, request):
        serializer = AssetCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        asset_type = get_object_or_404(
            AssetType.objects.filter(Q(created_by__isnull=True) | Q(created_by=request.user.profile)),
            pk=data["asset_type"].pk,
        )

        asset = AssetService.create_custom_asset(
            profile=request.user.profile,
            asset_type=asset_type,
            name=data["name"],
            symbol=data.get("symbol", ""),
            description=data.get("description", ""),
            data=data.get("data") or {},
            is_active=data.get("is_active", True),
        )
        return Response(AssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class AssetDetailView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(
            Asset.objects.select_related("asset_type", "owner__user").filter(
                Q(owner__isnull=True) | Q(owner=request.user.profile)
            ),
            pk=pk,
        )

    def get(self, request, pk):
        asset = self.get_object(request, pk)
        return Response(AssetSerializer(asset).data)

    def patch(self, request, pk):
        asset = self.get_object(request, pk)
        serializer = AssetUpdateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        asset_type = None
        if "asset_type" in data:
            asset_type = get_object_or_404(
                AssetType.objects.filter(Q(created_by__isnull=True) | Q(created_by=request.user.profile)),
                pk=data["asset_type"].pk,
            )

        asset = AssetService.update_asset(
            asset=asset,
            profile=request.user.profile,
            asset_type=asset_type,
            name=data.get("name"),
            symbol=data.get("symbol"),
            description=data.get("description"),
            data=data.get("data"),
            is_active=data.get("is_active"),
        )
        return Response(AssetSerializer(asset).data)

    def delete(self, request, pk):
        asset = self.get_object(request, pk)
        AssetService.deactivate_asset(asset=asset, profile=request.user.profile)
        return Response(status=status.HTTP_204_NO_CONTENT)
