from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Holding
from analytics.models import (
    Analytic,
    AnalyticDimension,
    AnalyticResult,
    AssetDimensionExposure,
    DimensionBucket,
    HoldingDimensionExposureOverride,
)
from analytics.serializers import (
    AnalyticCreateSerializer,
    AnalyticPatchSerializer,
    AnalyticResultSerializer,
    AnalyticRunSerializer,
    AnalyticSerializer,
    AssetExposureSerializer,
    AssetExposureUpsertItemSerializer,
    BucketCreateSerializer,
    BucketPatchSerializer,
    BucketSerializer,
    DimensionCreateSerializer,
    DimensionPatchSerializer,
    DimensionSerializer,
    HoldingOverrideSerializer,
    HoldingOverrideUpsertItemSerializer,
)
from analytics.services import AnalyticsEngine
from assets.models import Asset
from portfolios.models import Portfolio


def _owned_analytic_or_404(*, analytic_id: int, user):
    return get_object_or_404(
        Analytic.objects.select_related("portfolio__profile"),
        id=analytic_id,
        portfolio__profile__user=user,
    )


def _owned_dimension_or_404(*, dimension_id: int, user):
    return get_object_or_404(
        AnalyticDimension.objects.select_related("analytic__portfolio__profile"),
        id=dimension_id,
        analytic__portfolio__profile__user=user,
    )


def _owned_bucket_or_404(*, bucket_id: int, user):
    return get_object_or_404(
        DimensionBucket.objects.select_related("dimension__analytic__portfolio__profile"),
        id=bucket_id,
        dimension__analytic__portfolio__profile__user=user,
    )


def _owned_asset_exposure_or_404(*, exposure_id: int, user):
    return get_object_or_404(
        AssetDimensionExposure.objects.select_related("dimension__analytic__portfolio__profile"),
        id=exposure_id,
        dimension__analytic__portfolio__profile__user=user,
    )


def _owned_holding_override_or_404(*, override_id: int, user):
    return get_object_or_404(
        HoldingDimensionExposureOverride.objects.select_related("dimension__analytic__portfolio__profile"),
        id=override_id,
        dimension__analytic__portfolio__profile__user=user,
    )


class AnalyticListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analytics = (
            Analytic.objects.filter(portfolio__profile__user=request.user)
            .select_related("portfolio")
            .prefetch_related("dimensions")
            .order_by("portfolio_id", "name")
        )
        return Response(AnalyticSerializer(analytics, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AnalyticCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        portfolio = get_object_or_404(
            Portfolio,
            id=serializer.validated_data["portfolio_id"],
            profile__user=request.user,
        )

        analytic = Analytic(
            portfolio=portfolio,
            name=serializer.validated_data["name"],
            label=serializer.validated_data["label"],
            description=serializer.validated_data.get("description"),
            value_identifier=serializer.validated_data.get("value_identifier", "current_value"),
            is_system=False,
        )

        try:
            analytic.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AnalyticSerializer(analytic).data, status=status.HTTP_201_CREATED)


class AnalyticDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        return Response(AnalyticSerializer(analytic).data, status=status.HTTP_200_OK)

    def patch(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        serializer = AnalyticPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(analytic, field, value)

        try:
            analytic.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AnalyticSerializer(analytic).data, status=status.HTTP_200_OK)

    def delete(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        try:
            analytic.delete()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalyticRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        run = AnalyticsEngine.compute(analytic=analytic, triggered_by=request.user)
        return Response(AnalyticRunSerializer(run).data, status=status.HTTP_201_CREATED)


class AnalyticLatestResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)

        run = analytic.runs.filter(status="success").first()
        if not run:
            return Response({"detail": "No successful analytic run exists yet."}, status=status.HTTP_404_NOT_FOUND)

        results = (
            AnalyticResult.objects.filter(run=run)
            .select_related("dimension", "bucket")
            .order_by("dimension__display_order", "-total_value")
        )

        grouped = {}
        for result in results:
            dim_id = result.dimension_id
            if dim_id not in grouped:
                grouped[dim_id] = {
                    "dimension_id": dim_id,
                    "dimension_name": result.dimension.name if result.dimension else None,
                    "rows": [],
                }
            grouped[dim_id]["rows"].append(AnalyticResultSerializer(result).data)

        payload = {
            "analytic_id": analytic.id,
            "run": AnalyticRunSerializer(run).data,
            "dimensions": list(grouped.values()),
        }

        return Response(payload, status=status.HTTP_200_OK)


class DimensionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        dimensions = analytic.dimensions.prefetch_related("buckets").all()
        return Response(DimensionSerializer(dimensions, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, analytic_id: int):
        analytic = _owned_analytic_or_404(analytic_id=analytic_id, user=request.user)
        serializer = DimensionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dimension = AnalyticDimension(
            analytic=analytic,
            name=serializer.validated_data["name"],
            label=serializer.validated_data["label"],
            description=serializer.validated_data.get("description"),
            dimension_type=serializer.validated_data["dimension_type"],
            source_type=serializer.validated_data["source_type"],
            source_identifier=serializer.validated_data.get("source_identifier") or None,
            display_order=serializer.validated_data.get("display_order", 0),
        )

        try:
            dimension.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DimensionSerializer(dimension).data, status=status.HTTP_201_CREATED)


class DimensionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        serializer = DimensionPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(dimension, field, value)

        try:
            dimension.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DimensionSerializer(dimension).data, status=status.HTTP_200_OK)

    def delete(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        dimension.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BucketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        buckets = dimension.buckets.select_related("parent").all()
        return Response(BucketSerializer(buckets, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        serializer = BucketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parent = None
        parent_id = serializer.validated_data.get("parent_id")
        if parent_id:
            parent = get_object_or_404(DimensionBucket, id=parent_id, dimension=dimension)

        bucket = DimensionBucket(
            dimension=dimension,
            key=serializer.validated_data["key"],
            label=serializer.validated_data["label"],
            parent=parent,
            is_unknown_bucket=serializer.validated_data.get("is_unknown_bucket", False),
            is_active=serializer.validated_data.get("is_active", True),
            display_order=serializer.validated_data.get("display_order", 0),
        )

        try:
            bucket.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BucketSerializer(bucket).data, status=status.HTTP_201_CREATED)


class BucketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, bucket_id: int):
        bucket = _owned_bucket_or_404(bucket_id=bucket_id, user=request.user)
        serializer = BucketPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if "parent_id" in serializer.validated_data:
            parent_id = serializer.validated_data.pop("parent_id")
            if parent_id is None:
                bucket.parent = None
            else:
                bucket.parent = get_object_or_404(DimensionBucket, id=parent_id, dimension=bucket.dimension)

        for field, value in serializer.validated_data.items():
            setattr(bucket, field, value)

        try:
            bucket.save()
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(BucketSerializer(bucket).data, status=status.HTTP_200_OK)

    def delete(self, request, bucket_id: int):
        bucket = _owned_bucket_or_404(bucket_id=bucket_id, user=request.user)
        bucket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssetExposureListUpsertView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        qs = dimension.asset_exposures.select_related("asset", "bucket").order_by("asset_id", "bucket__display_order")
        return Response(AssetExposureSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        if dimension.dimension_type != dimension.DimensionType.WEIGHTED:
            return Response({"detail": "Asset exposures are only valid for weighted dimensions."}, status=status.HTTP_400_BAD_REQUEST)

        items = request.data if isinstance(request.data, list) else request.data.get("items")
        if not isinstance(items, list):
            return Response({"detail": "Payload must be a list or include an 'items' list."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AssetExposureUpsertItemSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)

        upserted = []
        for item in serializer.validated_data:
            asset = get_object_or_404(Asset, id=item["asset_id"])
            bucket = get_object_or_404(DimensionBucket, id=item["bucket_id"], dimension=dimension)
            exposure, _ = AssetDimensionExposure.objects.update_or_create(
                dimension=dimension,
                asset=asset,
                bucket=bucket,
                defaults={"weight": item["weight"], "source": AssetDimensionExposure.Source.USER},
            )
            upserted.append(exposure)

        return Response(AssetExposureSerializer(upserted, many=True).data, status=status.HTTP_200_OK)


class AssetExposureDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, exposure_id: int):
        exposure = _owned_asset_exposure_or_404(exposure_id=exposure_id, user=request.user)
        exposure.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HoldingOverrideListUpsertView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        qs = dimension.holding_exposure_overrides.select_related("holding", "bucket").order_by("holding_id", "bucket__display_order")
        return Response(HoldingOverrideSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, dimension_id: int):
        dimension = _owned_dimension_or_404(dimension_id=dimension_id, user=request.user)
        if dimension.dimension_type != dimension.DimensionType.WEIGHTED:
            return Response({"detail": "Holding overrides are only valid for weighted dimensions."}, status=status.HTTP_400_BAD_REQUEST)

        items = request.data if isinstance(request.data, list) else request.data.get("items")
        if not isinstance(items, list):
            return Response({"detail": "Payload must be a list or include an 'items' list."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HoldingOverrideUpsertItemSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)

        upserted = []
        for item in serializer.validated_data:
            holding = get_object_or_404(
                Holding,
                id=item["holding_id"],
                account__portfolio=dimension.analytic.portfolio,
            )
            bucket = get_object_or_404(DimensionBucket, id=item["bucket_id"], dimension=dimension)

            override, _ = HoldingDimensionExposureOverride.objects.update_or_create(
                dimension=dimension,
                holding=holding,
                bucket=bucket,
                defaults={"weight": item["weight"]},
            )
            upserted.append(override)

        return Response(HoldingOverrideSerializer(upserted, many=True).data, status=status.HTTP_200_OK)


class HoldingOverrideDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, override_id: int):
        override = _owned_holding_override_or_404(override_id=override_id, user=request.user)
        override.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
