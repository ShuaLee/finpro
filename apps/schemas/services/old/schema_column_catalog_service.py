from collections import defaultdict

from django.db.models import Prefetch

from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from assets.models.core import AssetType


class SchemaColumnCatalogService:
    """
    Provides the catalog of available SchemaColumnTemplates
    that may be added to a schema, grouped by category.

    Rules:
    - Includes ALL system-defined column templates
    - Excludes identifiers already present in the schema
    - Filters by asset-type compatibility (via behaviours)
    - Groups results by SchemaColumnCategory
    """

    @staticmethod
    def list_available_grouped(*, schema):
        """
        Return available SchemaColumnTemplates grouped by category.

        Returns:
            Dict[str, List[SchemaColumnTemplate]]
        """

        # --------------------------------------------------
        # 1. Identifiers already present in schema
        # --------------------------------------------------
        existing_identifiers = set(
            schema.columns.values_list("identifier", flat=True)
        )

        # --------------------------------------------------
        # 2. Asset types allowed by this account type
        # --------------------------------------------------
        allowed_asset_types = AssetType.objects.filter(
            account_types=schema.account_type
        )

        # --------------------------------------------------
        # 3. Base queryset: system templates with category
        # --------------------------------------------------
        templates = (
            SchemaColumnTemplate.objects.filter(
                is_system=True,
                category__isnull=False,
            )
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "behaviours",
                    queryset=SchemaColumnTemplateBehaviour.objects.filter(
                        asset_type__in=allowed_asset_types
                    ),
                )
            )
            .order_by(
                "category__display_order",
                "category__name",
                "identifier",
            )
        )

        # --------------------------------------------------
        # 4. Exclude identifiers already in schema
        # --------------------------------------------------
        if existing_identifiers:
            templates = templates.exclude(
                identifier__in=existing_identifiers
            )

        # --------------------------------------------------
        # 5. Filter by asset-type compatibility
        # --------------------------------------------------
        grouped = defaultdict(list)

        for template in templates:
            # behaviours are already prefiltered by asset type
            if not template.behaviours.all():
                continue

            category_key = template.category.identifier
            grouped[category_key].append(template)

        return dict(grouped)
