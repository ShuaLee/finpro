"""
users.views.status
~~~~~~~~~~~~~~~~~~
Provides an endpoint to check the authentication status of the user.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_status(request):
    """
    Check if the user is authenticated.

    Returns:
        JSON response with {"isAuthenticated": True} if valid token is provided.
    """
    logger.debug(f"Cookies: {request.COOKIES}")
    return Response({"isAuthenticated": True})
