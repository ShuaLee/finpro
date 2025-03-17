from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from .serializers import PortfolioSerializer

# Create your views here.


class PortfolioViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def me(self, request):
        profile = request.user.profile
        portfolio = profile.portfolio
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data)

     # Override list to return 404 for /portfolio/
    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
