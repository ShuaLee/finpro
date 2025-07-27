from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from schemas.models.core import Schema, SchemaColumnValue
from schemas.serializers.schemas import (
    SchemaDetailSerializer,
    AddCustomColumnSerializer,
    AddCalculatedColumnSerializer,
    SchemaColumnValueSerializer
)
from schemas.services.schema import add_custom_column, add_calculated_column
from schemas.services.value import update_column_value


class SchemaDetailView(generics.RetrieveAPIView):
    """
    GET /api/schemas/<schema_id>/
    Fetch schema details including all columns.
    """
    permission_classes = [IsAuthenticated]
    queryset = Schema.objects.all()
    serializer_class = SchemaDetailSerializer


class AddCustomColumnView(generics.GenericAPIView):
    """
    POST /api/schemas/<schema_id>/columns/
    Add a new custom column to a schema.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddCustomColumnSerializer

    def post(self, request, schema_id):
        schema = get_object_or_404(Schema, id=schema_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = add_custom_column(schema, **serializer.validated_data)
        return Response({"id": column.id, "title": column.title}, status=status.HTTP_201_CREATED)


class AddCalculatedColumnView(generics.GenericAPIView):
    """
    POST /api/schemas/<schema_id>/calculated-columns/
    Add a calculated column with formula.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddCalculatedColumnSerializer

    def post(self, request, schema_id):
        schema = get_object_or_404(Schema, id=schema_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = add_calculated_column(schema, **serializer.validated_data)
        return Response({"id": column.id, "title": column.title, "formula": column.formula}, status=status.HTTP_201_CREATED)


class UpdateColumnValueView(generics.UpdateAPIView):
    """
    PATCH /api/schemas/values/<value_id>/
    Update a schema column value for an account/holding.
    """
    permission_classes = [IsAuthenticated]
    queryset = SchemaColumnValue.objects.all()
    serializer_class = SchemaColumnValueSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        new_value = request.data.get("value")
        try:
            updated_instance = update_column_value(instance, new_value)
            return Response(self.get_serializer(updated_instance).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
