from __future__ import annotations

from django.db import transaction

from analytics.models import Analytic, AnalyticDimension, DimensionBucket


STARTER_ANALYTICS = [
    {
        "analytic": {
            "name": "allocation_overview",
            "label": "Allocation Overview",
            "description": "Core allocation starter analytics.",
            "value_identifier": "current_value",
        },
        "dimensions": [
            {
                "name": "asset_currency",
                "label": "Asset Currency",
                "description": "Allocation by each holding asset currency.",
                "dimension_type": AnalyticDimension.DimensionType.CATEGORICAL,
                "source_type": AnalyticDimension.SourceType.SCV_IDENTIFIER,
                "source_identifier": "asset_currency",
                "display_order": 1,
                "buckets": [
                    {
                        "key": "unknown",
                        "label": "Unknown",
                        "is_unknown_bucket": True,
                        "display_order": 999,
                    }
                ],
            },
            {
                "name": "asset_class_mix",
                "label": "Asset Class Mix",
                "description": "Weighted buckets for asset class allocation.",
                "dimension_type": AnalyticDimension.DimensionType.WEIGHTED,
                "source_type": AnalyticDimension.SourceType.ASSET_EXPOSURE,
                "display_order": 2,
                "buckets": [
                    {"key": "equity", "label": "Equity", "display_order": 1},
                    {"key": "crypto", "label": "Crypto", "display_order": 2},
                    {"key": "real_estate", "label": "Real Estate", "display_order": 3},
                    {"key": "commodity", "label": "Commodity", "display_order": 4},
                    {"key": "precious_metal", "label": "Precious Metal", "display_order": 5},
                    {"key": "custom", "label": "Custom", "display_order": 6},
                    {
                        "key": "unknown",
                        "label": "Unknown",
                        "is_unknown_bucket": True,
                        "display_order": 999,
                    },
                ],
            },
        ],
    },
    {
        "analytic": {
            "name": "energy_exposure",
            "label": "Energy Exposure",
            "description": "Starter energy taxonomy including fossil and green breakdowns.",
            "value_identifier": "current_value",
        },
        "dimensions": [
            {
                "name": "energy_mix",
                "label": "Energy Mix",
                "description": "Weighted energy allocation with nested buckets.",
                "dimension_type": AnalyticDimension.DimensionType.WEIGHTED,
                "source_type": AnalyticDimension.SourceType.ASSET_EXPOSURE,
                "display_order": 1,
                "buckets": [
                    {"key": "fossil", "label": "Fossil Fuels", "display_order": 1},
                    {"key": "coal", "label": "Coal", "parent_key": "fossil", "display_order": 2},
                    {"key": "coal_thermal", "label": "Coal - Thermal", "parent_key": "coal", "display_order": 3},
                    {"key": "coal_metallurgical", "label": "Coal - Metallurgical", "parent_key": "coal", "display_order": 4},
                    {"key": "oil_gas", "label": "Oil & Gas", "parent_key": "fossil", "display_order": 5},
                    {"key": "green", "label": "Green Energy", "display_order": 6},
                    {"key": "solar", "label": "Solar", "parent_key": "green", "display_order": 7},
                    {"key": "wind", "label": "Wind", "parent_key": "green", "display_order": 8},
                    {"key": "hydro", "label": "Hydro", "parent_key": "green", "display_order": 9},
                    {"key": "nuclear", "label": "Nuclear", "display_order": 10},
                    {
                        "key": "unknown",
                        "label": "Unknown",
                        "is_unknown_bucket": True,
                        "display_order": 999,
                    },
                ],
            }
        ],
    },
]


@transaction.atomic
def seed_starter_templates_for_portfolio(*, portfolio_id: int) -> dict[str, int]:
    created_analytics = 0
    created_dimensions = 0
    created_buckets = 0

    for analytic_template in STARTER_ANALYTICS:
        analytic_defaults = {
            "label": analytic_template["analytic"]["label"],
            "description": analytic_template["analytic"].get("description"),
            "value_identifier": analytic_template["analytic"].get("value_identifier", "current_value"),
            "is_active": True,
            "is_system": False,
        }
        analytic, analytic_created = Analytic.objects.get_or_create(
            portfolio_id=portfolio_id,
            name=analytic_template["analytic"]["name"],
            defaults=analytic_defaults,
        )
        if analytic_created:
            created_analytics += 1

        for dimension_template in analytic_template["dimensions"]:
            dimension_defaults = {
                "label": dimension_template["label"],
                "description": dimension_template.get("description"),
                "dimension_type": dimension_template["dimension_type"],
                "source_type": dimension_template["source_type"],
                "source_identifier": dimension_template.get("source_identifier"),
                "display_order": dimension_template.get("display_order", 0),
                "is_active": True,
            }
            dimension, dimension_created = AnalyticDimension.objects.get_or_create(
                analytic=analytic,
                name=dimension_template["name"],
                defaults=dimension_defaults,
            )
            if dimension_created:
                created_dimensions += 1

            bucket_map: dict[str, DimensionBucket] = {}
            for bucket_template in dimension_template.get("buckets", []):
                if bucket_template.get("is_unknown_bucket"):
                    unknown = dimension.buckets.filter(is_unknown_bucket=True).first()
                    if unknown:
                        bucket_map[bucket_template["key"]] = unknown
                        continue

                bucket, bucket_created = DimensionBucket.objects.get_or_create(
                    dimension=dimension,
                    key=bucket_template["key"],
                    defaults={
                        "label": bucket_template["label"],
                        "is_unknown_bucket": bucket_template.get("is_unknown_bucket", False),
                        "display_order": bucket_template.get("display_order", 0),
                        "is_active": True,
                    },
                )
                if bucket_created:
                    created_buckets += 1
                bucket_map[bucket_template["key"]] = bucket

            for bucket_template in dimension_template.get("buckets", []):
                parent_key = bucket_template.get("parent_key")
                if not parent_key:
                    continue

                bucket = bucket_map.get(bucket_template["key"])
                parent = bucket_map.get(parent_key)
                if not bucket or not parent:
                    continue
                if bucket.parent_id != parent.id:
                    bucket.parent = parent
                    bucket.save(update_fields=["parent"])

    return {
        "analytics_created": created_analytics,
        "dimensions_created": created_dimensions,
        "buckets_created": created_buckets,
    }
