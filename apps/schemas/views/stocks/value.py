from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from schemas.models import StockPortfolioSCV
from schemas.serializers.stocks import StockPortfolioSCVEditSerializer


class StockSCVEditView(generics.UpdateAPIView):
    """
    PATCH /api/v1/schemas/stocks/scv/<id>/edit/
    Edit a value for a schema column in a holding.
    """
    permission_classes = [IsAuthenticated]
    queryset = StockPortfolioSCV.objects.all()
    serializer_class = StockPortfolioSCVEditSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return self.queryset.filter(
            column__schema__stock_portfolio__portfolio__profile=self.request.user.profile
        )
