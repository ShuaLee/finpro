from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import SelfManagedAccount
from schemas.models import SchemaColumnValue


class SchemaHoldingsView(APIView):
    """
    Returns schema-style tabular data for holdings under a SelfManagedAccount.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id):
        account = get_object_or_404(SelfManagedAccount, pk=account_id)

        # Permission check
        if account.stock_portfolio.portfolio.profile.user != request.user:
            return Response({"error": "Unauthorized"}, status=403)

        # Step 1: Get active schema & holdings
        schema = account.active_schema
        holdings = account.holdings.select_related('stock').all()
        columns = schema.columns.all()

        # 🧠 Get content type for StockHolding model
        from assets.models import StockHolding
        ct = ContentType.objects.get_for_model(StockHolding)

        # Step 2: Loop holdings and fetch column values
        rows = []
        for holding in holdings:
            row = {
                "holding_id": holding.id,
                "stock": {
                    "ticker": holding.stock.ticker,
                    "name": holding.stock.name
                },
                "values": {}
            }

            for column in columns:
                value_qs = SchemaColumnValue.objects.filter(
                    column=column,
                    account_ct=ct,            # ✅ your custom field
                    account_id=holding.id     # ✅ your custom field
                ).first()
                row["values"][column.title] = value_qs.value if value_qs else None

            rows.append(row)

        return Response({
            "schema_id": schema.id,
            "columns": [col.title for col in columns],
            "data": rows
        })
