from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_status(request):
    logger.debug(f"Cookies: {request.COOKIES}")
    return Response({"isAuthenticated": True})
