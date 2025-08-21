# from django.contrib.contenttypes.models import ContentType
# from django.shortcuts import get_object_or_404
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from accounts.models import SelfManagedAccount
# from schemas.models import SchemaColumnVisibility
# from schemas.services.column_value_resolver import resolve_column_value


# class SchemaHoldingsView(APIView):
#     """
#     Returns schema-style tabular data for holdings under a SelfManagedAccount.
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request, account_id):
#         account = get_object_or_404(SelfManagedAccount, pk=account_id)

#         # 🔐 Permission check
#         if account.stock_portfolio.portfolio.profile.user != request.user:
#             return Response({"error": "Unauthorized"}, status=403)

#         schema = account.active_schema
#         if not schema:
#             return Response({"error": "No active schema found."}, status=404)

#         holdings = account.holdings.select_related("stock").all()
#         all_columns = list(schema.columns.all())

#         # 🚫 Apply per-account visibility filter
#         account_ct = ContentType.objects.get_for_model(account)
#         hidden_column_ids = SchemaColumnVisibility.objects.filter(
#             content_type=account_ct,
#             object_id=account.id,
#             is_visible=False
#         ).values_list("column_id", flat=True)

#         # ✅ Apply visibility filter and sort by display_order
#         visible_columns = [
#             col for col in all_columns if col.id not in hidden_column_ids
#         ]
#         visible_columns.sort(key=lambda col: col.display_order)

#         # 🧱 Build data response
#         rows = []
#         for holding in holdings:
#             row = {
#                 "holding_id": holding.id,
#                 "stock": {
#                     "ticker": holding.stock.ticker,
#                     "name": holding.stock.name
#                 },
#                 "values": {}
#             }

#             for column in visible_columns:
#                 value = resolve_column_value(
#                     holding, column, fallback_to_default=True)
#                 row["values"][column.title] = value

#             rows.append(row)

#         return Response({
#             "schema_id": schema.id,
#             "columns": [
#                 {
#                     "id": col.id,
#                     "title": col.title,
#                     "data_type": col.data_type,
#                     "editable": col.editable,
#                     "source": col.source,
#                     "decimal_places": col.decimal_places,
#                     "is_system": col.is_system,
#                     "scope": col.scope,
#                     "display_order": col.display_order,
#                 }
#                 for col in visible_columns
#             ],
#             "data": rows
#         })
