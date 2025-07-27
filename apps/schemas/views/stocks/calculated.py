from rest_framework.response import Response
from rest_framework import status
from schemas.models import StockPortfolioSchema
from schemas.views.base import BaseSchemaView
from schemas.services import add_calculated_column


class StockAddCalculatedColumnView(BaseSchemaView):
    """
    POST /api/v1/schemas/stocks/<schema_id>/calculated-columns/
    Add a calculated column with a formula.
    """
    schema_model = StockPortfolioSchema
    portfolio_attr = 'stock_portfolio'

    def post(self, request, schema_id):
        title = request.data.get("title")
        formula = request.data.get("formula")

        if not title or not formula:
            return Response({"detail": "Title and formula are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        schema = self.get_schema(schema_id, request.user)

        try:
            column = add_calculated_column(schema, title, formula)
            return Response({"id": column.id, "title": column.title, "formula": column.formula},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
