from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from .models import Portfolio
from .serializers import PortfolioSerializer

# Create your views here.


class PortfolioViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return Portfolio.objects.filter(profile_id=profile_id)

    def get_object(self):
        """
        Retrieve the single IndividualPortfolio for the given profile.
        """
        profile_id = self.kwargs['profile_pk']
        return Portfolio.objects.get(profile_id=profile_id)
