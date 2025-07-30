from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.utils.country_currency_catalog import (
    get_common_country_choices,
    get_common_currency_choices,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def preferences_metadata_view(request):
    """
    Returns metadata for supported countries and currencies.
    Example response:
    {
        "countries": [{"code": "US", "name": "United States"}, ...],
        "currencies": [{"code": "USD", "name": "US Dollar"}, ...]
    }
    """
    countries = [{"code": code, "name": name} for code, name in get_common_country_choices()]
    currencies = [{"code": code, "name": name} for code, name in get_common_currency_choices()]

    return Response({
        "countries": countries,
        "currencies": currencies
    })
