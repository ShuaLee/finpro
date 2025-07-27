# schemas/views/stocks/schema_viewset.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from assets.constants import ASSET_SCHEMA_CONFIG
from schemas.models import StockPortfolioSchema
from schemas.services import add_calculated_column


class StockSchemaViewSet(viewsets.ViewSet):
    """
    Handles:
    - GET /schemas/stocks/{id}/ → schema detail
    - POST /schemas/stocks/{id}/columns/ → add column
    - POST /schemas/stocks/{id}/calculated-columns/ → add calculated column
    """

    permission_classes = [IsAuthenticated]

    def get_schema(self, schema_id, user):
        try:
            schema = StockPortfolioSchema.objects.get(id=schema_id)
        except StockPortfolioSchema.DoesNotExist:
            return None
        if schema.stock_portfolio.portfolio.profile != user.profile:
            return None
        return schema

    def retrieve(self, request, pk=None):
        schema = self.get_schema(pk, request.user)
        if not schema:
            return Response({"detail": "Schema not found or unauthorized."}, status=404)

        column_model = schema.columns.model
        asset_type = getattr(column_model, 'ASSET_TYPE', None)
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {})

        existing = schema.columns.all()
        existing_keys = {(col.source, col.source_field) for col in existing}

        available_fields = []
        for source, fields in config.items():
            for source_field, field_config in fields.items():
                if (source, source_field) not in existing_keys:
                    available_fields.append({
                        "title": source_field.replace("_", " ").title(),
                        "source": source,
                        "source_field": source_field,
                        "data_type": field_config["data_type"],
                        "editable": field_config.get("editable", True)
                    })

        existing_columns = [{
            "id": col.id,
            "title": col.title,
            "source": col.source,
            "source_field": col.source_field,
            "editable": col.editable,
            "is_deletable": col.is_deletable,
            "data_type": col.data_type
        } for col in existing]

        return Response({
            "schema_id": schema.id,
            "existing_columns": existing_columns,
            "available_columns": available_fields
        })

    @action(detail=True, methods=['post'], url_path='columns')
    def add_column(self, request, pk=None):
        schema = self.get_schema(pk, request.user)
        if not schema:
            return Response({"detail": "Schema not found or unauthorized."}, status=404)

        source = request.data.get("source")
        source_field = request.data.get("source_field")
        custom_title = request.data.get("title")

        if not source or not source_field:
            return Response({"detail": "Both 'source' and 'source_field' are required."}, status=400)

        column_model = schema.columns.model
        asset_type = getattr(column_model, 'ASSET_TYPE', None)
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {}).get(source, {})
        field_config = config.get(source_field)

        if not field_config:
            return Response({"detail": "Invalid source or source_field."}, status=400)

        title = custom_title or source_field.replace("_", " ").title()
        column, created = column_model.objects.get_or_create(
            schema=schema,
            source=source,
            source_field=source_field,
            defaults={
                "title": title,
                "data_type": field_config["data_type"],
                "editable": field_config.get("editable", True),
                "decimal_spaces": field_config.get("decimal_spaces"),
                "formula": field_config.get("formula", "")
            }
        )

        return Response({"id": column.id, "title": column.title, "created": created})

    @action(detail=True, methods=['post'], url_path='calculated-columns')
    def add_calculated_column(self, request, pk=None):
        schema = self.get_schema(pk, request.user)
        if not schema:
            return Response({"detail": "Schema not found or unauthorized."}, status=404)

        title = request.data.get("title")
        formula = request.data.get("formula")

        if not title or not formula:
            return Response({"detail": "Title and formula are required."}, status=400)

        try:
            column = add_calculated_column(schema, title, formula)
            return Response({"id": column.id, "title": column.title, "formula": column.formula}, status=201)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
