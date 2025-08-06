from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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
)
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
        portfolio_owner = getattr(
            schema.portfolio.profile.user,
            'id',
            None
        )

        if portfolio_owner != request.user.id:
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


class SchemaColumnViewSet(mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = SchemaColumn.objects.all()
    serializer_class = SchemaColumnSerializer
    permission_classes = [IsAuthenticated]


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
        if hasattr(holding, 'account') and holding.account.stock_portfolio.portfolio.profile.user != user:
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
