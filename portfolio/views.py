from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PortfolioSerializer

# Create your views here.
class PortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio = request.user.profile.portfolio
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data)