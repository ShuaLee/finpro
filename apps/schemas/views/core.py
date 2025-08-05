from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
)
from schemas.serializers import (
    SchemaDetailSerializer,
    SchemaColumnSerializer,
    SchemaColumnValueSerializer,
    AddCustomColumnSerializer,
    AddCalculatedColumnSerializer,
)


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
        serializer = AddCalculatedColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        column = SchemaColumn.objects.create(
            schema=schema,
            title=data['title'],
            formula=data['formula'],
            data_type='decimal',  # 🧠 Assuming all formulas resolve to decimal
            source='calculated',
            editable=False,
            is_deletable=True
        )

        return Response(SchemaColumnSerializer(column).data, status=status.HTTP_201_CREATED)


class SchemaColumnValueViewSet(mixins.UpdateModelMixin,
                               mixins.RetrieveModelMixin,
                               viewsets.GenericViewSet):
    """
    Handles updating SchemaColumnValue objects. Assumes they already exist.
    """
    queryset = SchemaColumnValue.objects.select_related("column")
    serializer_class = SchemaColumnValueSerializer
