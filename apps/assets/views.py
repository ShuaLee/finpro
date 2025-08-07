from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from assets.models.base import InvestmentTheme, HoldingThemeValue


class InvestmentThemeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        themes = InvestmentTheme.objects.filter(
            portfolio_id=portfolio_id,
            portfolio__profile__user=request.user
        )
        return Response([
            {
                "id": theme.id,
                "name": str(theme),
            } for theme in themes
        ])


class UpdateHoldingThemeValueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        holding = ...  # Your logic to get holding from ID
        theme = ...    # Your logic to get InvestmentTheme
        value = request.data.get("value")
        data_type = request.data.get("data_type")

        htv, _ = HoldingThemeValue.objects.get_or_create(
            holding_ct=ContentType.objects.get_for_model(holding),
            holding_id=holding.id,
            theme=theme
        )
        htv.set_value(value, data_type)
        htv.save()
        return Response({"success": True})
