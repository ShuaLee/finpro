from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from assets.constants import ASSET_SCHEMA_CONFIG
from schemas.models.stocks import StockPortfolioSchema

# Create your views here.


class SchemaView(APIView):
    permission_classes = [IsAuthenticated]

    def get_schema(self, schema_id, user):
        try:
            schema = StockPortfolioSchema.objects.get(id=schema_id)
            if schema.stock_portfolio.portfolio.profile != user.profile:
                raise PermissionDenied("Unauthorized")
            return schema
        except StockPortfolioSchema.DoesNotExist:
            raise ValidationError("Schema not found.")

    def get(self, request, schema_id):
        try:
            schema = StockPortfolioSchema.objects.get(id=schema_id)
        except StockPortfolioSchema.DoesNotExist:
            return Response({"detail": "Schema not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate user owns the schema
        if schema.stock_portfolio.portfolio.profile != request.user.profile:
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

        column_model = schema.columns.model
        asset_type = getattr(column_model, 'ASSET_TYPE', None)

        if not asset_type:
            return Response({"detail": "Asset type not defined for this schema."}, status=status.HTTP_400_BAD_REQUEST)

        config = ASSET_SCHEMA_CONFIG.get(asset_type, {})

        # Collect already existing column keys
        existing = schema.columns.all()
        existing_keys = set((col.source, col.source_field) for col in existing)

        # Discover available fields from config
        available_fields = []
        for source, fields in config.items():
            for source_field, field_config in fields.items():
                key = (source, source_field)
                if key not in existing_keys:
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
            "asset_type": asset_type,
            "existing_columns": existing_columns,
            "available_columns": available_fields,
        })

    def post(self, request, schema_id):
        schema = self.get_schema(schema_id, request.user)
        source = request.data.get("source")
        source_field = request.data.get("source_field")
        custom_title = request.data.get("title")

        if not source or not source_field:
            return Response(
                {"detail": "Both 'source' and 'source_field' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        column_model = schema.columns.model
        asset_type = getattr(column_model, 'ASSET_TYPE', None)
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {}).get(source, {})
        field_config = config.get(source_field)

        if not field_config:
            return Response({"detail": "Invalid source or source_field."}, status=400)

        title = custom_title or source_field.replace(
            "_", " ").title()  # fallback title

        column, created = column_model.objects.get_or_create(
            schema=schema,
            source=source,
            source_field=source_field,
            defaults={
                "title": title,
                "data_type": field_config["data_type"],
                "editable": field_config.get("editable", True),
                "decimal_spaces": field_config.get("decimal_spaces"),
                "formula": field_config.get("formula", ""),
            }
        )

        return Response({
            "id": column.id,
            "title": column.title,
            "created": created
        })

    def delete(self, request, schema_id):
        schema = self.get_schema(schema_id, request.user)
        column_id = request.data.get("column_id")

        try:
            column = schema.columns.get(id=column_id)
            if not column.is_deletable:
                return Response({"detail": "This column cannot be deleted."}, status=403)
            column.delete()
            return Response({"detail": "Column deleted."})
        except schema.columns.model.DoesNotExist:
            return Response({"detail": "Column not found in this schema."}, status=404)
