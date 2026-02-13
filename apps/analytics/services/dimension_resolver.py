from dataclasses import dataclass
from decimal import Decimal

from analytics.models.exposure import AssetDimensionExposure, HoldingDimensionExposureOverride
from analytics.services.value_service import ValueResolverService

@dataclass
class BucketContribution:
    bucket_id: int | None
    label: str
    weight: Decimal

class DimensionResolverService:
    UNKNOWN_LABEL = "Unknown"

    @staticmethod
    def resolve_contributions(*, holding, dimension):
        if dimension.dimension_type == dimension.DimensionType.CATEGORICAL:
            return DimensionResolverService._resolve_categorical(
                holding=holding,
                dimension=dimension,
            )

        return DimensionResolverService._resolve_weighted(
            holding=holding,
            dimension=dimension,
        )

    @staticmethod
    def _resolve_categorical(*, holding, dimension):
        identifier = dimension.source_identifier
        value = (
            ValueResolverService.get_text(
                holding=holding,
                identifier=identifier,
            )
            if identifier
            else None
        )
        label = str(value).strip() if value else ""
        if not label:
            label = DimensionResolverService._unknown_label(dimension=dimension)

        return [
            BucketContribution(
                bucket_id=None,
                label=label,
                weight=Decimal("1"),
            )
        ]

    @staticmethod
    def _resolve_weighted(*, holding, dimension):
        overrides = list(
            HoldingDimensionExposureOverride.objects.filter(
                dimension=dimension,
                holding=holding,
                bucket__is_active=True,
            ).select_related("bucket")
        )

        if overrides:
            return DimensionResolverService._to_contributions(
                exposures=overrides,
                dimension=dimension,
            )

        if not holding.asset_id:
            return DimensionResolverService._unknown_contribution(dimension=dimension)

        asset_exposures = list(
            AssetDimensionExposure.objects.filter(
                dimension=dimension,
                asset=holding.asset,
                bucket__is_active=True,
            ).select_related("bucket")
        )

        if not asset_exposures:
            return DimensionResolverService._unknown_contribution(dimension=dimension)

        return DimensionResolverService._to_contributions(
            exposures=asset_exposures,
            dimension=dimension,
        )

    @staticmethod
    def _to_contributions(*, exposures, dimension):
        contributions = []
        total = Decimal("0")

        for exposure in exposures:
            weight = Decimal(str(exposure.weight or 0))
            if weight <= 0:
                continue

            contributions.append(
                BucketContribution(
                    bucket_id=exposure.bucket_id,
                    label=exposure.bucket.label,
                    weight=weight,
                )
            )
            total += weight

        if not contributions:
            return DimensionResolverService._unknown_contribution(dimension=dimension)

        if total < Decimal("1"):
            contributions.extend(
                DimensionResolverService._unknown_contribution(
                    dimension=dimension,
                    weight=(Decimal("1") - total),
                )
            )

        return contributions

    @staticmethod
    def _unknown_contribution(*, dimension, weight=Decimal("1")):
        unknown = dimension.buckets.filter(is_unknown_bucket=True).first()
        label = unknown.label if unknown else DimensionResolverService.UNKNOWN_LABEL
        bucket_id = unknown.id if unknown else None

        return [
            BucketContribution(
                bucket_id=bucket_id,
                label=label,
                weight=weight,
            )
        ]

    @staticmethod
    def _unknown_label(*, dimension):
        unknown = dimension.buckets.filter(is_unknown_bucket=True).first()
        return unknown.label if unknown else DimensionResolverService.UNKNOWN_LABEL
