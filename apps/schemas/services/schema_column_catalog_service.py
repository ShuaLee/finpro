from django.db.models import Q

from schemas.models.schema_column_template import SchemaColumnTemplate
from assets.models.core import AssetType


class SchemaColumnCatalogService:
    """
    Provides the catalog of available SchemaColumnTemplates
    that may be added to a schema.

    Rules:
    - Includes ALL system-defined column templates (default or optional)
    - Excludes identifiers already present in the schema
    - Filters by asset-type compatibility
    """

    @staticmethod
    def list_available(*, schema):
        """
        Return SchemaColumnTemplates that may be added to this schema.
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
        account_type = schema.account_type
        allowed_asset_types = AssetType.objects.filter(
            account_types=account_type
        )

        # --------------------------------------------------
        # 3. Base queryset: all system column templates
        # --------------------------------------------------
        templates = SchemaColumnTemplate.objects.filter(
            is_system=True
        ).select_related("template")

        # --------------------------------------------------
        # 4. Restrict to:
        #    - template-scoped columns for this account type
        #    - OR global system columns (template=None)
        # --------------------------------------------------
        templates = templates.filter(
            Q(template__account_type=account_type) |
            Q(template__isnull=True)
        )

        # --------------------------------------------------
        # 5. Exclude identifiers already in schema
        # --------------------------------------------------
        if existing_identifiers:
            templates = templates.exclude(
                identifier__in=existing_identifiers
            )

        # --------------------------------------------------
        # 6. Asset-type compatibility filter
        # --------------------------------------------------
        compatible_templates = []

        for template in templates:
            behaviours = template.behaviours.filter(
                asset_type__in=allowed_asset_types
            )

            if behaviours.exists():
                compatible_templates.append(template)

        return compatible_templates
