from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from common.utils.country_data import get_country_choices, get_currency_choices


@api_view(['GET'])
@permission_classes([AllowAny])  # No auth required
def metadata_view(request):
    """
    Returns metadata for countries and currencies.
    Example response:
    {
        "countries": [{"code": "US", "name": "United States"}, ...],
        "currencies": [{"code": "USD", "name": "US Dollar"}, ...]
    }
    """
    countries = [{"code": code, "name": name} for code, name in get_country_choices()]
    currencies = [{"code": code, "name": name} for code, name in get_currency_choices()]
    return Response({
        "countries": countries,
        "currencies": currencies
    })
