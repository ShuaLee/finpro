from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models.stocks import ManagedAccount
from .models import StockPortfolio
from .serializers import PortfolioSerializer

# Create your views here.
class PortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio = request.user.profile.portfolio
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data)
    
class StockPortfolioDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            stock_portfolio = StockPortfolio.objects.get(
                portfolio=request.user.profile.portfolio
            )
        except StockPortfolio.DoesNotExist:
            return Response({"detail": "Stock portfolio not found."}, status=404)
        
        # Serialize self-managed accounts (with schema data)
        self_managed_accounts = []
        total_self_managed_value = 0

        for account in stock_portfolio.self_managed_accounts.select_related('active_schema').prefetch_related(
            'holdings__stock',
            'holdings__column_values__column'
        ):
            schema = account.active_schema
            if not schema:
                continue

            columns = schema.columns.all()
            holdings_data = []

            for holding in account.holdings.all():
                row = {}
                for col in columns:
                    val = next(
                        (cv for cv in holding.column_values.all() if cv.column_id == col.id),
                        None
                    )
                    row[col.title] = val.get_value() if val else None
                holdings_data.append(row)

            value = float(account.get_current_value_in_profile_fx() or 0)
            total_self_managed_value += value

            self_managed_accounts.append({
                'account_id': account.id,
                'account_name': account.name,
                'schema_name': schema.name,
                'current_value_fx': value,
                'columns': [col.title for col in columns],
                'holdings': holdings_data,
            })

        # Serialize managed accounts
        managed_accounts = ManagedAccount.objects.filter(
            stock_portfolio=stock_portfolio
        ).select_related('stock_portfolio')

        managed_data = []
        total_managed_value = 0

        for acct in managed_accounts:
            value_fx = float(acct.get_total_current_value_in_profile_fx() or 0)
            total_managed_value += value_fx
            managed_data.append({
                'account_id': acct.id,
                'account_name': acct.name,
                'current_value': float(acct.current_value),
                'invested_amount': float(acct.invested_amount),
                'currency': acct.currency,
                'current_value_fx': value_fx,
            })

        return Response({
            'total_self_managed_value_fx': round(total_self_managed_value, 2),
            'total_managed_value_fx': round(total_managed_value, 2),
            'total_combined_value_fx': round(total_self_managed_value + total_managed_value, 2),
            'self_managed_accounts': self_managed_accounts,
            'managed_accounts': managed_data,
        })