from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.stocks import StockAccount
from schemas.models import SchemaColumnVisibility
from schemas.services.column_value_resolver import resolve_column_value


class SchemaHoldingsView(APIView):
    """
    Returns schema-style tabular data for holdings under a self-managed StockAccount.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id):
        account = get_object_or_404(StockAccount, pk=account_id)

        # ✅ Ensure self-managed (cannot edit/view schema grid for managed accounts)
        if account.account_mode != "self_managed":
            return Response({"error": "Schema grid is only available for self-managed accounts."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 🔐 Permission check
        if account.stock_portfolio.portfolio.profile.user != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        schema = getattr(account, "active_schema", None)
        if not schema:
            return Response({"error": "No active schema found."}, status=status.HTTP_404_NOT_FOUND)

        holdings = account.holdings.select_related("stock").all()
        all_columns = list(schema.columns.all())

        # 🚫 Apply per-account visibility filter
        account_ct = ContentType.objects.get_for_model(StockAccount)
        hidden_column_ids = SchemaColumnVisibility.objects.filter(
            content_type=account_ct,
            object_id=account.id,
            is_visible=False,
        ).values_list("column_id", flat=True)

        # ✅ Apply visibility filter and sort by display_order
        visible_columns = [col for col in all_columns if col.id not in hidden_column_ids]
        visible_columns.sort(key=lambda col: (col.display_order or 0))

        # 🧱 Build data response
        rows = []
        for holding in holdings:
            row = {
                "holding_id": holding.id,
                "stock": {
                    "ticker": holding.stock.ticker,
                    "name": holding.stock.name,
                },
                "values": {},
            }

            for column in visible_columns:
                value = resolve_column_value(holding, column, fallback_to_default=True)
                row["values"][column.title] = value

            rows.append(row)

        return Response({
            "schema_id": schema.id,
            "columns": [
                {
                    "id": col.id,
                    "title": col.title,
                    "data_type": col.data_type,
                    "editable": col.editable,
                    "source": col.source,
                    "decimal_places": col.decimal_places,
                    "is_system": col.is_system,
                    "scope": col.scope,
                    "display_order": col.display_order,
                }
                for col in visible_columns
            ],
            "data": rows,
        }, status=status.HTTP_200_OK)
