from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class BaseSchemaView(APIView):
    """
    Base for schema-related views. Subclasses must define:
    - schema_model (e.g., StockPortfolioSchema)
    - portfolio_attr (e.g., "stock_portfolio")
    """
    permission_classes = [IsAuthenticated]
    schema_model = None
    portfolio_attr = None

    def get_schema(self, schema_id, user):
        if not self.schema_model or not self.portfolio_attr:
            raise NotImplementedError(
                "Must set schema_model and portfolio_attr in subclass.")

        try:
            schema = self.schema_model.objects.get(id=schema_id)
        except self.schema_model.DoesNotExist:
            raise NotFound("Schema not found.")

        profile = getattr(user, 'profile', None)
        portfolio = getattr(schema, self.portfolio_attr)
        schema_owner = portfolio.portfolio.profile

        if profile != schema_owner:
            raise PermissionDenied("You do not have access to this schema.")

        return schema
