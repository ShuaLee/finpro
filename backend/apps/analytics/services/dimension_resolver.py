from dataclasses import dataclass
from decimal import Decimal

from analytics.models.dimension import DimensionBucket
from analytics.services.value_service import ValueResolverService


@dataclass
class BucketContribution:
    bucket_id: int | None
    label: str
    weight: Decimal


class DimensionResolverService:
    UNKNOWN_LABEL = "Unknown"

    @staticmethod
    def resolve_contributions(
        *,
        holding,
        dimension,
        values_by_holding,
        asset_exposures_by_asset,
        override_exposures_by_holding,
    ):
        if dimension.dimension_type == dimension.DimensionType.CATEGORICAL:
            return DimensionResolverService._resolve_categorical(
                holding_id=holding.id,
                dimension=dimension,
                values_by_holding=values_by_holding,
            )

        return DimensionResolverService._resolve_weighted(
            holding=holding,
            dimension=dimension,
            asset_exposures_by_asset=asset_exposures_by_asset,
            override_exposures_by_holding=override_exposures_by_holding,
        )

    @staticmethod
    def _resolve_categorical(*, holding_id, dimension, values_by_holding):
        value = ValueResolverService.get_text(
            holding_id=holding_id,
            identifier=dimension.source_identifier,
            values_by_holding=values_by_holding,
        )

        label = str(value).strip() if value else ""
        if not label:
            return DimensionResolverService._unknown_contribution(dimension=dimension)

        bucket = DimensionBucket.objects.filter(
            dimension=dimension,
            key=label.lower().replace(" ", "-"),
            is_active=True,
        ).first()

        return [
            BucketContribution(
                bucket_id=bucket.id if bucket else None,
                label=label,
                weight=Decimal("1"),
            )
        ]

    @staticmethod
    def _resolve_weighted(*, holding, dimension, asset_exposures_by_asset, override_exposures_by_holding):
        overrides = override_exposures_by_holding.get(holding.id, [])
        if overrides:
            return DimensionResolverService._to_contributions(
                exposures=overrides,
                dimension=dimension,
            )

        if not holding.asset_id:
            return DimensionResolverService._unknown_contribution(dimension=dimension)

        asset_exposures = asset_exposures_by_asset.get(holding.asset_id, [])
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

        return [BucketContribution(bucket_id=bucket_id, label=label, weight=weight)]
