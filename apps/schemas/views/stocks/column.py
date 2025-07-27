from rest_framework import status
from rest_framework.response import Response
from assets.constants import ASSET_SCHEMA_CONFIG
from schemas.models import StockPortfolioSchema
from schemas.views.base import BaseSchemaView


class StockAddColumnView(BaseSchemaView):
    """
    POST /api/v1/schemas/stocks/<schema_id>/columns/
    Add a predefined column.
    """
    schema_model = StockPortfolioSchema
    portfolio_attr = 'stock_portfolio'

    def post(self, request, schema_id):
        schema = self.get_schema(schema_id, request.user)
        source = request.data.get("source")
        source_field = request.data.get("source_field")
        custom_title = request.data.get("title")

        if not source or not source_field:
            return Response({"detail": "Both source and source_field are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        column_model = schema.columns.model
        asset_type = getattr(column_model, 'ASSET_TYPE', None)
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {}).get(source, {})
        field_config = config.get(source_field)

        if not field_config:
            return Response({"detail": "Invalid source or source_field."}, status=status.HTTP_400_BAD_REQUEST)

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

        return Response(
            {"id": column.id, "title": column.title, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
