from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.config.utils import get_serialized_available_columns, get_available_config_columns
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
)
from schemas.serializers import (
    SchemaDetailSerializer,
    SchemaColumnSerializer,
    SchemaColumnReorderSerializer,
    SchemaColumnValueSerializer,
    AddCustomColumnSerializer,
    AddCalculatedColumnSerializer,
    AddFromConfigSerializer,
)
from schemas.permissions import is_schema_owner, is_holding_owner
from schemas.services.column_value_resolver import cast_value


class SchemaViewSet(mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    queryset = Schema.objects.prefetch_related("columns").all()
    serializer_class = SchemaDetailSerializer

    @action(detail=True, methods=["post"])
    def add_custom_column(self, request, pk=None):
        schema = self.get_object()
        serializer = AddCustomColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        column = SchemaColumn.objects.create(
            schema=schema,
            title=data['title'],
            source='custom',
            data_type=data['data_type'],
            editable=True,
            is_deletable=True
        )
        return Response(SchemaColumnSerializer(column).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_calculated_column(self, request, pk=None):
        schema = self.get_object()
        serializer = AddCalculatedColumnSerializer(data=request.data, context={"schema": schema})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 🛠️ Auto-create missing variables as editable custom columns
        for var in data["missing_variables"]:
            SchemaColumn.objects.create(
                schema=schema,
                title=var.replace("_", " ").title(),
                data_type="decimal",
                source="custom",
                source_field=var,
                editable=True,
                is_deletable=True,
            )

        # ✅ Now create the calculated column
        col = SchemaColumn.objects.create(
            schema=schema,
            title=data["title"],
            data_type="decimal",
            source="calculated",
            formula_expression=data["formula"],
            editable=False,
            is_deletable=True,
        )

        return Response(SchemaColumnSerializer(col).data, status=201)

    @action(detail=True, methods=["patch"])
    def reorder_columns(self, request, pk=None):
        """
        PATCH /schemas/<id>/reorder_columns/

        {
            "columns": [
                { "id": 12, "display_order": 0 },
                { "id": 14, "display_order": 1 },
                ...
            ]
        }
        """
        schema = self.get_object()

        # 🔐 Permission check: Ensure current user owns the portfolio
        if not is_schema_owner(request.user, schema):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        column_data = request.data.get("columns", [])

        # Validate structure
        for entry in column_data:
            serializer = SchemaColumnReorderSerializer(data=entry)
            serializer.is_valid(raise_exception=True)

        # Fetch all columns once
        columns = {col.id: col for col in schema.columns.all()}

        for entry in column_data:
            col_id = entry["id"]
            if col_id in columns:
                col = columns[col_id]
                col.display_order = entry["display_order"]
                col.save()

        return Response({"success": True, "reordered": len(column_data)}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"])
    def add_from_config(self, request, pk=None):
        """
        POST /schemas/<id>/add_from_config/
        {
            "columns": [
                { "source": "asset", "source_field": "price" },
                { "source": "holding", "source_field": "purchase_price" },
                ...
            ]
        }
        """
        schema = self.get_object()
        data = request.data.get("columns", [])

        if not isinstance(data, list):
            return Response({"error": "Expected 'columns' to be a list."}, status=400)

        # ✅ Map of allowed columns: {(source, source_field): meta}
        available = {
            (source, field): meta
            for source, field, meta in get_available_config_columns(schema)
        }

        created = []

        for item in data:
            source = item.get("source")
            field = item.get("source_field")

            if not source or not field:
                continue  # Skip malformed

            meta = available.get((source, field))
            if not meta:
                continue  # Already exists or unknown

            column = SchemaColumn.objects.create(
                schema=schema,
                title=meta.get("title", field.replace("_", " ").title()),
                source=source,
                source_field=field,
                field_path=meta.get("field_path"),  # Now that you're storing it!
                data_type=meta["data_type"],
                editable=meta.get("editable", True),
                is_deletable=meta.get("is_deletable", True),
                decimal_places=meta.get("decimal_places"),
                formula_method=meta.get("formula_method"),
                formula_expression=meta.get("formula_expression"),
            )
            created.append(column)

        return Response({
            "added": len(created),
            "columns": SchemaColumnSerializer(created, many=True).data
        }, status=201)



class SchemaColumnViewSet(mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = SchemaColumn.objects.all()
    serializer_class = SchemaColumnSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_deletable and not instance.editable:
            return Response({"error": "This column is not editable."}, status=403)
        
        # Extra protection: prevent updating formula if it's backend-defined
        if instance.source == "calculated" and instance.formula_method:
            return Response({"error": "Backend-calculated column can't be edited."}, status=403)
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_deletable:
            return Response({"error": "This column cannot be deleted."}, status=403)
        instance.delete()
        return Response(status=204)


class SchemaColumnValueViewSet(mixins.UpdateModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    queryset = SchemaColumnValue.objects.select_related("column")
    serializer_class = SchemaColumnValueSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        user = request.user
        holding = instance.account  # GenericForeignKey resolves here
        column = instance.column

        # 🔐 Permission check
        if not is_holding_owner(user, holding):
            return Response({"error": "Unauthorized"}, status=403)

        value = request.data.get("value")
        if column.source == "holding":
            setattr(holding, column.source_field, cast_value(value, column))
            holding.save()
        else:
            instance.value = value
            instance.is_edited = True
            instance.save()

        return Response({"success": True})

class SchemaAvailableColumnsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schema_id):
        schema = get_object_or_404(Schema, pk=schema_id)
        return Response(get_serialized_available_columns(schema))
    

class SchemaFormulaVariableListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schema_id):
        schema = get_object_or_404(Schema, pk=schema_id)

        # Check ownership
        if not is_schema_owner(request.user, schema):
            return Response({"error": "Unauthorized"}, status=403)

        schema_type = schema.schema_type
        config = SCHEMA_CONFIG_REGISTRY.get(schema_type, {})

        variables = []

        for source, fields in config.items():
            for field_key, meta in fields.items():
                variables.append({
                    "name": field_key,
                    "title": meta.get("title", field_key.replace("_", " ").title()),
                    "source": source,
                    "data_type": meta.get("data_type"),
                })

        return Response({
            "schema_id": schema.id,
            "asset_type": schema_type,
            "variables": variables
        })
