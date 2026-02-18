from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AssetsHealthView(APIView):
    """
    Placeholder assets endpoint while legacy theme views are rebuilt.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Assets app is online."}, status=200)
