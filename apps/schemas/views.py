from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility,
)
from schemas.serializers import (
    SchemaDetailSerializer,
    SchemaColumnSerializer,
    SchemaColumnValueSerializer,
    AddCustomColumnSerializer,
    AddCalculatedColumnSerializer,
)
from django.shortcuts import get_object_or_404


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


class SchemaColumnVisibilityToggleViewSet(viewsets.ViewSet):
    """
    Allows toggling column visibility on a per-account basis.
    """

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """
        Expects:
        {
            "account_type": "selfmanagedaccount",
            "account_id": 12,
            "column_id": 5,
            "visible": true
        }
        """
        account_type = request.data.get("account_type")
        account_id = request.data.get("account_id")
        column_id = request.data.get("column_id")
        visible = request.data.get("visible", True)

        if not all([account_type, account_id, column_id]):
            return Response({"error": "Missing required fields"}, status=400)

        try:
            content_type = ContentType.objects.get(model=account_type.lower())
            column = SchemaColumn.objects.get(pk=column_id)
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid account_type"}, status=400)
        except SchemaColumn.DoesNotExist:
            return Response({"error": "Invalid column_id"}, status=400)

        vis_obj, _ = SchemaColumnVisibility.objects.get_or_create(
            content_type=content_type,
            object_id=account_id,
            column=column,
            defaults={"is_visible": visible}
        )

        if vis_obj.is_visible != visible:
            vis_obj.is_visible = visible
            vis_obj.save()

        return Response({
            "column_id": column.id,
            "account_type": account_type,
            "account_id": account_id,
            "is_visible": vis_obj.is_visible
        }, status=200)
