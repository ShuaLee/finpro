from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assets.models import AssetType, CustomAsset, RealEstateAsset, RealEstateType
from assets.serializers import (
    AssetTypeCreateSerializer,
    AssetTypeSerializer,
    AssetTypeUpdateSerializer,
    CustomAssetCreateSerializer,
    CustomAssetSerializer,
    CustomAssetUpdateSerializer,
    RealEstateAssetCreateSerializer,
    RealEstateAssetSerializer,
    RealEstateAssetUpdateSerializer,
    RealEstateTypeCreateSerializer,
    RealEstateTypeSerializer,
    RealEstateTypeUpdateSerializer,
)
from assets.services import (
    CustomAssetService,
    RealEstateAssetService,
    RealEstateTypeService,
)
from profiles.services.bootstrap_service import ProfileBootstrapService


def _profile_for_user(user):
    try:
        return user.profile
    except ObjectDoesNotExist:
        return ProfileBootstrapService.bootstrap(user=user)


class AssetsHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Assets app is online."}, status=status.HTTP_200_OK)


class AssetTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _profile_for_user(request.user)
        queryset = AssetType.objects.filter(created_by__isnull=True) | AssetType.objects.filter(created_by=profile)
        queryset = queryset.order_by("name")
        return Response(AssetTypeSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class CustomAssetTypeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = _profile_for_user(request.user)
        serializer = AssetTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset_type = AssetType(
            name=serializer.validated_data["name"],
            created_by=profile,
        )
        try:
            asset_type.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AssetTypeSerializer(asset_type).data, status=status.HTTP_201_CREATED)


class CustomAssetTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, type_id: int):
        profile = _profile_for_user(request.user)
        asset_type = get_object_or_404(AssetType, id=type_id, created_by=profile)
        serializer = AssetTypeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if "name" in serializer.validated_data:
            asset_type.name = serializer.validated_data["name"]
        try:
            asset_type.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AssetTypeSerializer(asset_type).data, status=status.HTTP_200_OK)

    def delete(self, request, type_id: int):
        profile = _profile_for_user(request.user)
        asset_type = get_object_or_404(AssetType, id=type_id, created_by=profile)
        try:
            asset_type.delete()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomAssetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _profile_for_user(request.user)
        queryset = (
            CustomAsset.objects.filter(owner=profile)
            .select_related("asset__asset_type", "currency")
            .order_by("-created_at")
        )
        return Response(CustomAssetSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = _profile_for_user(request.user)
        serializer = CustomAssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            custom_asset = CustomAssetService.create(
                profile=profile,
                name=serializer.validated_data["name"],
                asset_type_slug=serializer.validated_data["asset_type_slug"],
                currency_code=serializer.validated_data["currency_code"],
                requires_review=serializer.validated_data["requires_review"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CustomAssetSerializer(custom_asset).data, status=status.HTTP_201_CREATED)


class CustomAssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        profile = _profile_for_user(request.user)
        custom_asset = get_object_or_404(
            CustomAsset.objects.select_related("asset__asset_type", "currency"),
            pk=asset_id,
            owner=profile,
        )
        return Response(CustomAssetSerializer(custom_asset).data, status=status.HTTP_200_OK)

    def patch(self, request, asset_id):
        profile = _profile_for_user(request.user)
        custom_asset = get_object_or_404(CustomAsset, pk=asset_id, owner=profile)
        serializer = CustomAssetUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            custom_asset = CustomAssetService.update(
                custom_asset=custom_asset,
                name=serializer.validated_data.get("name"),
                currency_code=serializer.validated_data.get("currency_code"),
                requires_review=serializer.validated_data.get("requires_review"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CustomAssetSerializer(custom_asset).data, status=status.HTTP_200_OK)

    def delete(self, request, asset_id):
        profile = _profile_for_user(request.user)
        custom_asset = get_object_or_404(CustomAsset, pk=asset_id, owner=profile)
        CustomAssetService.delete(custom_asset=custom_asset)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RealEstateTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _profile_for_user(request.user)
        queryset = RealEstateType.objects.filter(created_by__isnull=True) | RealEstateType.objects.filter(created_by=profile)
        queryset = queryset.order_by("name")
        return Response(RealEstateTypeSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class RealEstateTypeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = _profile_for_user(request.user)
        serializer = RealEstateTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            obj = RealEstateTypeService.create_custom(
                profile=profile,
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description", ""),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RealEstateTypeSerializer(obj).data, status=status.HTTP_201_CREATED)


class RealEstateTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, type_id: int):
        profile = _profile_for_user(request.user)
        obj = get_object_or_404(RealEstateType, id=type_id, created_by=profile)
        serializer = RealEstateTypeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            obj = RealEstateTypeService.update_custom(
                real_estate_type=obj,
                name=serializer.validated_data.get("name"),
                description=serializer.validated_data.get("description"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RealEstateTypeSerializer(obj).data, status=status.HTTP_200_OK)

    def delete(self, request, type_id: int):
        profile = _profile_for_user(request.user)
        obj = get_object_or_404(RealEstateType, id=type_id, created_by=profile)
        try:
            RealEstateTypeService.delete_custom(real_estate_type=obj)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RealEstateAssetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _profile_for_user(request.user)
        queryset = (
            RealEstateAsset.objects.filter(owner=profile)
            .select_related("property_type", "country", "currency")
            .order_by("property_type__name", "city")
        )
        return Response(RealEstateAssetSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = _profile_for_user(request.user)
        serializer = RealEstateAssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asset = RealEstateAssetService.create(
                profile=profile,
                property_type_id=serializer.validated_data["property_type_id"],
                country_code=serializer.validated_data["country_code"],
                currency_code=serializer.validated_data["currency_code"],
                city=serializer.validated_data.get("city", ""),
                address=serializer.validated_data.get("address", ""),
                notes=serializer.validated_data.get("notes", ""),
                is_owner_occupied=serializer.validated_data["is_owner_occupied"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RealEstateAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class RealEstateAssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        profile = _profile_for_user(request.user)
        asset = get_object_or_404(
            RealEstateAsset.objects.select_related("property_type", "country", "currency"),
            pk=asset_id,
            owner=profile,
        )
        return Response(RealEstateAssetSerializer(asset).data, status=status.HTTP_200_OK)

    def patch(self, request, asset_id):
        profile = _profile_for_user(request.user)
        asset = get_object_or_404(RealEstateAsset, pk=asset_id, owner=profile)
        serializer = RealEstateAssetUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asset = RealEstateAssetService.update(
                real_estate_asset=asset,
                profile=profile,
                property_type_id=serializer.validated_data.get("property_type_id"),
                country_code=serializer.validated_data.get("country_code"),
                currency_code=serializer.validated_data.get("currency_code"),
                city=serializer.validated_data.get("city"),
                address=serializer.validated_data.get("address"),
                notes=serializer.validated_data.get("notes"),
                is_owner_occupied=serializer.validated_data.get("is_owner_occupied"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RealEstateAssetSerializer(asset).data, status=status.HTTP_200_OK)

    def delete(self, request, asset_id):
        profile = _profile_for_user(request.user)
        asset = get_object_or_404(RealEstateAsset, pk=asset_id, owner=profile)
        RealEstateAssetService.delete(real_estate_asset=asset)
        return Response(status=status.HTTP_204_NO_CONTENT)
